import argparse
import os.path

from steg.steg import video_to_images


class Args(argparse.Namespace):
    input: str
    output_dir: str


def main():
    argparser = argparse.ArgumentParser(prog="video_frames")
    argparser.add_argument('input')
    argparser.add_argument('output_dir')
    args = argparser.parse_args(namespace=Args())

    video_to_images(args.input, os.path.join(args.output_dir, "output_%03d.png"))
