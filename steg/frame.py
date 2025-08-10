import math
import pathlib
import struct
from io import IOBase
from typing import Optional

from PIL import Image, ImageDraw

from steg.util import generate_default_palette, list_fuzzy_search, fuzzy_equals


class Frame:
    version: int
    frame_seqno: int
    width: int
    height: int
    tile_width: int
    tile_height: int
    body_length: int
    x: int
    y: int
    is_full: bool
    image: Image.Image
    drawable_image: ImageDraw.ImageDraw
    palette: list[tuple[int, int, int]]

    default_tile_width = 16
    default_tile_height = 16
    header_length_bytes = 13

    def __init__(self, frame_seqno: int, body_length: int, resolution: tuple[int, int], tile_width: int, tile_height: int, palette: Optional[list[tuple[int, int, int]]] = None, version: int = 1):
        self.version = version
        self.frame_seqno = frame_seqno
        self.body_length = body_length
        self.width, self.height = resolution
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.x = 0
        self.y = 0
        self.is_full = False

        if palette is not None:
            self.palette = palette
        else:
            self.palette = generate_default_palette()

    @classmethod
    def new(cls, frame_seqno: int, body_length: int, resolution: tuple[int, int], tile_width: int, tile_height: int, version: int = 1):
        frame = cls(frame_seqno, body_length, resolution, tile_width, tile_height, version=version)
        frame.image = Image.new('RGB', resolution)
        frame.drawable_image = ImageDraw.Draw(frame.image)

        frame.write_header()

        return frame

    @classmethod
    def load_from_file(cls, file_handle: str | bytes | pathlib.Path | IOBase):
        image = Image.open(file_handle)
        frame = cls(0, 0, (image.width, image.height), cls.default_tile_width, cls.default_tile_height)
        frame.image = image
        frame.drawable_image = ImageDraw.Draw(frame.image)

        return frame

    def __len__(self):
        return self.body_length

    def write(self, data: bytes | int) -> int:
        """

        :param data:
        :return: number of tiles that were drawn successfully
        """
        if self.is_full:
            return 0

        # convert byte(s) to tiles
        if isinstance(data, int):
            tiles = [self.tile_from_byte(data)]
        else:
            tiles = [self.tile_from_byte(byte) for byte in data]

        return self.draw_tiles(tiles)

    def draw_tiles(self, tiles: list[tuple[int, int, int]]) -> int:
        tiles_drawn = 0
        for tile_color in tiles:
            self.drawable_image.rectangle(xy=((self.x, self.y), (self.x + self.tile_width-1, self.y + self.tile_height-1)),
                                          fill=tile_color)
            tiles_drawn += 1

            self.x += self.tile_width
            if self.x + self.tile_width > self.width:
                self.x = 0
                self.y += self.tile_height
            if self.y + self.tile_height > self.height:
                self.is_full = True
                break

        return tiles_drawn

    def tile_from_byte(self, byte: int) -> tuple[int, int, int]:
        return self.palette[byte]

    def write_header(self):
        self.draw_tiles(self.generate_header(self.version, self.frame_seqno, self.tile_width, self.tile_height, self.body_length))

    def generate_header(self, version: int, frame_seqno: int, tile_width: int, tile_height: int, length: int) -> list[tuple[int, int, int]]:
        """
        header:
        magic bytes - black tile, white tile
        version - 1 byte
        reserved - 1 byte
        reserved - 1 byte
        frame_seqno - 1 byte
        tile width - 1 byte
        tile height - 1 byte
        body length - 2 bytes (big-endian) (does not include header)
        reserved - 3 bytes
        """
        length_bytes = struct.pack('>H', length)

        return [
            self.palette[0x0], self.palette[0xFF],  # magic bytes
            self.palette[version],
            self.palette[0x0], self.palette[0x0],  # reserved
            self.palette[frame_seqno],
            self.palette[tile_width],
            self.palette[tile_height],
            self.palette[length_bytes[0]],
            self.palette[length_bytes[1]],
            self.palette[0x0], self.palette[0x0], self.palette[0x0]  # reserved
        ]

    def decode(self, ignore_errors: bool = False) -> bytes:
        # find header -- starts with black
        # skip 8 rows and columns of pixels to try to avoid image edges
        if not fuzzy_equals(self.image.getpixel(xy=(8, 8)), self.palette[0x0]):
            raise Exception(f'failed to find header -- first tile should be 0 (palette color: {self.palette[0x0]})')

        # count the number of pixels til we see a color change (to white)
        black_tile_width = 0
        while black_tile_width < self.image.width:
            if fuzzy_equals(self.image.getpixel(xy=(black_tile_width+8, 8)), self.palette[0xFF]):
                break

            black_tile_width += 1
        else:
            raise Exception(f'failed to find magic bytes in header -- second tile should be 255 (palette color: {self.palette[0xFF]})')

        black_tile_width += 8

        # we use square tiles at the moment, so assume tile height is same as width
        self.tile_width = black_tile_width
        self.tile_height = black_tile_width

        # read rest of header starting from the center of the third tile
        self.x = math.ceil(self.tile_width * 2.5)
        self.y = math.ceil(self.tile_height / 2)
        header_bytes = self.read(self.header_length_bytes-2)
        self.version = header_bytes[0]
        # [1] reserved
        # [2] reserved
        self.frame_seqno = header_bytes[3]
        assert self.tile_width == header_bytes[4], f"ERROR: {self.tile_width} != {header_bytes[4]}"
        self.tile_height = header_bytes[5]
        self.body_length = (header_bytes[6] << 8) + header_bytes[7]
        # [8], [9], [10] reserved

        return self.read(ignore_errors=ignore_errors)

    def read(self, num_tiles_to_read: Optional[int] = None, ignore_errors: bool = False) -> bytes:
        num_tiles_read = 0
        pixels = []
        if num_tiles_to_read is None:
            num_tiles_to_read = self.body_length
        while num_tiles_read < num_tiles_to_read:
            if self.image.width - self.x < math.ceil(self.tile_width / 2):
                self.x = math.ceil(self.tile_width / 2)
                self.y += self.tile_height
                if self.image.height - self.y < math.ceil(self.tile_height / 2):
                    break

            pixel = self.image.getpixel((self.x, self.y))

            try:
                pixels.append(list_fuzzy_search(self.palette, pixel))
            except:
                if ignore_errors:
                    print(f"invalid tile {num_tiles_read} at ({self.x},{self.y}) {pixel}, ignoring")
                    pixels.append(0)
                else:
                    raise

            num_tiles_read += 1
            self.x += self.tile_width

        return bytes(pixels)
