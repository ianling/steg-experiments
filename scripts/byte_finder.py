import argparse
import glob
import os
import re

from steg.frame import Frame


class Args(argparse.Namespace):
    frames_path: str
    needle: str


def main():
    argparser = argparse.ArgumentParser(prog="byte finder")
    argparser.add_argument('frames_path')
    argparser.add_argument('needle')
    args = argparser.parse_args(namespace=Args())

    needle_bytes = bytes.fromhex(args.needle)

    frames = glob.glob(os.path.join(args.frames_path, '*.png'))
    frames = sorted(frames, key=lambda x: float(re.findall(r"(\d+)", x)[-1]))

    for frame_path in frames:
        frame = Frame.load_from_file(frame_path)
        decoded = frame.decode()
        try:
            index = decoded.index(needle_bytes)
        except ValueError:
            continue
        print(f"needle found in {frame_path} @ index {index}")

