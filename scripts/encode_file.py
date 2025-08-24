import argparse
import os.path
from steg.steg import encode, images_to_video


class Args(argparse.Namespace):
    input_file: str
    output: str
    fps: int
    width: int
    height: int
    tile_size: int


def main():
    argparser = argparse.ArgumentParser(prog="video_frames")
    argparser.add_argument('input_file')
    argparser.add_argument('output')
    argparser.add_argument('--fps', '-f', type=int, default=3)
    argparser.add_argument('--width', '-w', type=int, default=1280)
    argparser.add_argument('--height', '-H', type=int, default=720)
    argparser.add_argument('--tile_size', '-t', type=int, default=16)
    args = argparser.parse_args(namespace=Args())

    with open(args.input_file, 'rb') as f:
        encode(f.read(), output_path=args.output, resolution=(args.width, args.height), tile_width=args.tile_size, tile_height=args.tile_size)
    images_to_video(os.path.join(args.output, 'test_%03d.png'), os.path.join(args.output, 'out.mp4'), framerate=args.fps)
