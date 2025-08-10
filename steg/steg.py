import math
import pathlib

import ffmpeg  # type: ignore

from steg.frame import Frame
from steg.util import factors


VERSION = 1
HEADER_LENGTH_BYTES = 13


"""
ideas:
- command tiles
    - if a tile of a particular color is hit, it signals that the next e.g. 2 tiles are a command
        - example: a command to set the tile dimensions
        - example: a command to alter the tile palette
        - example: a command to skip the next n tiles (decorative tiles)
- improve fuzzy matching
    - calculate the distance to all the colors in the palette, sort by distance, pick the lowest if it meets a certain threshold?
* allow customizing the palette via a (256*3)-byte file. the first three bytes represent R, G, and B of the
    color assigned to the value 0,
* allow scrambling of the default palette in a 256-byte file. The first byte represents the 8-bit value assigned to the 
    first color in the default palette, and so on.
* allow scrambling of the default palette by way of a seed provided to a cryptographically secure RNG
* add optional extras to header, i.e. make header variable length

default palette 2025-04-06: [(0, 0, 42), (0, 0, 84), (0, 0, 126), (0, 0, 168), (0, 0, 210), (0, 0, 252), (0, 42, 0), (0, 42, 42), (0, 42, 84), (0, 42, 126), (0, 42, 168), (0, 42, 210), (0, 42, 252), (0, 84, 0), (0, 84, 42), (0, 84, 84), (0, 84, 126), (0, 84, 168), (0, 84, 210), (0, 84, 252), (0, 126, 0), (0, 126, 42), (0, 126, 84), (0, 126, 126), (0, 126, 168), (0, 126, 210), (0, 126, 252), (0, 168, 0), (0, 168, 42), (0, 168, 84), (0, 168, 126), (0, 168, 168), (0, 168, 210), (0, 168, 252), (0, 210, 0), (0, 210, 42), (0, 210, 84), (0, 210, 126), (0, 210, 168), (0, 210, 210), (0, 210, 252), (0, 252, 0), (0, 252, 42), (0, 252, 84), (0, 252, 126), (0, 252, 168), (0, 252, 210), (0, 252, 252), (42, 0, 0), (42, 0, 42), (42, 0, 84), (42, 0, 126), (42, 0, 168), (42, 0, 210), (42, 0, 252), (42, 42, 0), (42, 42, 42), (42, 42, 84), (42, 42, 126), (42, 42, 168), (42, 42, 210), (42, 42, 252), (42, 84, 0), (42, 84, 42), (42, 84, 84), (42, 84, 126), (42, 84, 168), (42, 84, 210), (42, 84, 252), (42, 126, 0), (42, 126, 42), (42, 126, 84), (42, 126, 126), (42, 126, 168), (42, 126, 210), (42, 126, 252), (42, 168, 0), (42, 168, 42), (42, 168, 84), (42, 168, 126), (42, 168, 168), (42, 168, 210), (42, 168, 252), (42, 210, 0), (42, 210, 42), (42, 210, 84), (42, 210, 126), (42, 210, 168), (42, 210, 210), (42, 210, 252), (42, 252, 0), (42, 252, 42), (42, 252, 84), (42, 252, 126), (42, 252, 168), (42, 252, 210), (42, 252, 252), (84, 0, 0), (84, 0, 42), (84, 0, 84), (84, 0, 126), (84, 0, 168), (84, 0, 210), (84, 0, 252), (84, 42, 0), (84, 42, 42), (84, 42, 84), (84, 42, 126), (84, 42, 168), (84, 42, 210), (84, 42, 252), (84, 84, 0), (84, 84, 42), (84, 84, 84), (84, 84, 126), (84, 84, 168), (84, 84, 210), (84, 84, 252), (84, 126, 0), (84, 126, 42), (84, 126, 84), (84, 126, 126), (84, 126, 168), (84, 126, 210), (84, 126, 252), (84, 168, 0), (84, 168, 42), (84, 168, 84), (84, 168, 126), (84, 168, 168), (84, 168, 210), (84, 168, 252), (84, 210, 0), (84, 210, 42), (84, 210, 84), (84, 210, 126), (84, 210, 168), (84, 210, 210), (84, 210, 252), (84, 252, 0), (84, 252, 42), (84, 252, 84), (84, 252, 126), (84, 252, 168), (84, 252, 210), (84, 252, 252), (126, 0, 0), (126, 0, 42), (126, 0, 84), (126, 0, 126), (126, 0, 168), (126, 0, 210), (126, 0, 252), (126, 42, 0), (126, 42, 42), (126, 42, 84), (126, 42, 126), (126, 42, 168), (126, 42, 210), (126, 42, 252), (126, 84, 0), (126, 84, 42), (126, 84, 84), (126, 84, 126), (126, 84, 168), (126, 84, 210), (126, 84, 252), (126, 126, 0), (126, 126, 42), (126, 126, 84), (126, 126, 126), (126, 126, 168), (126, 126, 210), (126, 126, 252), (126, 168, 0), (126, 168, 42), (126, 168, 84), (126, 168, 126), (126, 168, 168), (126, 168, 210), (126, 168, 252), (126, 210, 0), (126, 210, 42), (126, 210, 84), (126, 210, 126), (126, 210, 168), (126, 210, 210), (126, 210, 252), (126, 252, 0), (126, 252, 42), (126, 252, 84), (126, 252, 126), (126, 252, 168), (126, 252, 210), (126, 252, 252), (168, 0, 0), (168, 0, 42), (168, 0, 84), (168, 0, 126), (168, 0, 168), (168, 0, 210), (168, 0, 252), (168, 42, 0), (168, 42, 42), (168, 42, 84), (168, 42, 126), (168, 42, 168), (168, 42, 210), (168, 42, 252), (168, 84, 0), (168, 84, 42), (168, 84, 84), (168, 84, 126), (168, 84, 168), (168, 84, 210), (168, 84, 252), (168, 126, 0), (168, 126, 42), (168, 126, 84), (168, 126, 126), (168, 126, 168), (168, 126, 210), (168, 126, 252), (168, 168, 0), (168, 168, 42), (168, 168, 84), (168, 168, 126), (168, 168, 168), (168, 168, 210), (168, 168, 252), (168, 210, 0), (168, 210, 42), (168, 210, 84), (168, 210, 126), (168, 210, 168), (168, 210, 210), (168, 210, 252), (168, 252, 0), (168, 252, 42), (168, 252, 84), (168, 252, 126), (168, 252, 168), (168, 252, 210), (168, 252, 252), (210, 0, 0), (210, 0, 42), (210, 0, 84), (210, 0, 126), (210, 0, 168), (210, 0, 210), (210, 0, 252), (210, 42, 0), (210, 42, 42), (210, 42, 84), (210, 42, 126), (210, 42, 168), (210, 42, 210), (210, 42, 252), (210, 84, 0), (210, 84, 42), (210, 84, 84), (210, 84, 126), (210, 84, 168), (210, 84, 210), (210, 84, 252), (210, 126, 0), (210, 126, 42), (210, 126, 84), (210, 126, 126), (210, 126, 168), (210, 126, 210), (210, 126, 252), (210, 168, 0), (210, 168, 42), (210, 168, 84), (210, 168, 126), (210, 168, 168), (210, 168, 210), (210, 168, 252), (210, 210, 0), (210, 210, 42), (210, 210, 84), (210, 210, 126), (210, 210, 168), (210, 210, 210), (210, 210, 252), (210, 252, 0), (210, 252, 42), (210, 252, 84), (210, 252, 126), (210, 252, 168), (210, 252, 210), (210, 252, 252), (252, 0, 0), (252, 0, 42), (252, 0, 84), (252, 0, 126), (252, 0, 168), (252, 0, 210), (252, 0, 252), (252, 42, 0), (252, 42, 42), (252, 42, 84), (252, 42, 126), (252, 42, 168), (252, 42, 210), (252, 42, 252), (252, 84, 0), (252, 84, 42), (252, 84, 84), (252, 84, 126), (252, 84, 168), (252, 84, 210), (252, 84, 252), (252, 126, 0), (252, 126, 42), (252, 126, 84), (252, 126, 126), (252, 126, 168), (252, 126, 210), (252, 126, 252), (252, 168, 0), (252, 168, 42), (252, 168, 84), (252, 168, 126), (252, 168, 168), (252, 168, 210), (252, 168, 252), (252, 210, 0), (252, 210, 42), (252, 210, 84), (252, 210, 126), (252, 210, 168), (252, 210, 210), (252, 210, 252), (252, 252, 0), (252, 252, 42), (252, 252, 84), (252, 252, 126), (252, 252, 168), (252, 252, 210), (252, 252, 252)]
"""

def determine_tile_size(data_length: int, resolution: tuple[int, int]) -> tuple[int, int]:
    min_tile_width = 32
    min_tile_height = 32
    max_total_tiles_per_frame = (resolution[0] // min_tile_width) * (resolution[1] // min_tile_height)
    max_body_tiles_per_frame = max_total_tiles_per_frame - HEADER_LENGTH_BYTES

    # if we can't fit all the data in a single frame,
    # clamp the tile size to the minimum to fit as many as possible into each frame and minimize the number of frames
    if data_length >= max_body_tiles_per_frame:
        return min_tile_width, min_tile_height

    # ...otherwise, if we can fit it all in one frame, try to maximize the size of each tile to ensure data integrity.
    # make sure we take the header into account when determining the max size of the tiles
    tiles_to_draw_per_frame = data_length + HEADER_LENGTH_BYTES

    factorized = [x for x in factors(tiles_to_draw_per_frame)]

    if len(factorized) == 0:
        # the number of tiles to draw ended up being a prime number, add one to make it not prime and try again
        factorized = [x for x in factors(tiles_to_draw_per_frame + 1)]

    factorized_list_middle_index = len(factorized) // 2 - 1
    # TODO: find the pair of factors that most closely matches the aspect ratio of the image? right now it's just grabbing from the middle
    small_axis_num_tiles, large_axis_num_tiles = factorized[
                                                 factorized_list_middle_index:factorized_list_middle_index + 2]
    max_tile_width = max(min_tile_width, resolution[0] // large_axis_num_tiles)
    max_tile_height = max(min_tile_height, resolution[1] // small_axis_num_tiles)
    tile_scale = max_tile_width if max_tile_width < max_tile_height else max_tile_height
    # this function only returns square dimensions
    return tile_scale, tile_scale


def encode(data: bytes, resolution: tuple[int, int] = (1280, 720), tile_width: int = None, tile_height: int = None, output_path: str = "./") -> list[str]:
    """
    Encodes the given data into one or more images, writing them as files.

    The tile width/height are constrained to a minimum of 1 and a maximum that depends on the resolution given.
    The full header (13 bytes) and at least one data tile must fit in each image.

    :param data: the data to encode
    :param resolution: the desired resolution of each image
    :param tile_width: the width in pixels of each byte tile
    :param tile_height: the height in pixels of each byte tile
    :param output_path: the path to write encoded image files to
    :return: a list of relative paths to the encoded image files
    """
    total_data_length = len(data)

    if not tile_width or not tile_height:
        tile_width, tile_height = determine_tile_size(total_data_length, resolution)

    tiles_to_draw_per_frame = (resolution[0] // tile_width) * (resolution[1] // tile_height) - HEADER_LENGTH_BYTES
    if tiles_to_draw_per_frame >= total_data_length:
        tiles_to_draw_per_frame = total_data_length
    expected_total_num_frames = math.ceil(total_data_length / tiles_to_draw_per_frame)

    frame_seqno = 0
    frame_num = 1
    frame = Frame.new(frame_seqno, tiles_to_draw_per_frame, resolution, tile_width, tile_height)

    saved_frame_paths = []
    for byte in data:
        if frame.write(byte) == 0:
            path = pathlib.Path(output_path, f'test_{frame_num:03d}.png')
            frame.image.save(path)
            frame.image.close()
            saved_frame_paths.append(path)
            frame_num += 1

            frame_seqno = (frame_seqno + 1) % 256
            if frame_num == expected_total_num_frames:
                # calculate number of tiles that will be drawn on the final frame
                tiles_to_draw_per_frame = total_data_length - (tiles_to_draw_per_frame * (expected_total_num_frames-1))
            frame = Frame.new(frame_seqno, tiles_to_draw_per_frame, resolution, tile_width, tile_height)
            frame.write(byte)

    # make sure the last frame gets saved if it wasn't automatically
    if not frame.is_full:
        path = pathlib.Path(output_path, f'test_{frame_num:03d}.png')
        frame.image.save(path)
        frame.image.close()
        saved_frame_paths.append(path)

    return saved_frame_paths


def video_to_images(video_path: str, output_path: str):
    (
        ffmpeg
        .input(video_path)
        .output(output_path)
        .run()
    )


def images_to_video(image_file_names_wildcard: str, output_path: str, framerate: int = 20):
    (
        ffmpeg
        .input(image_file_names_wildcard, framerate=framerate)
        .output(output_path, vcodec='libx264', video_bitrate='200k', crf=28, **{'x264-params': 'keyint=1:scenecut=0'})  # TODO: testing values here for bitrate and crf
        .run()
    )
