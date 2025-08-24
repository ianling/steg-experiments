import argparse
from steg.frame import Frame
import sys


class Args(argparse.Namespace):
    file: str
    output: str
    raw: str


def main():
    argparser = argparse.ArgumentParser(prog="decode_frame")
    argparser.add_argument('file')
    argparser.add_argument('-o', '--output')
    argparser.add_argument('-r', '--raw', action='store_true')
    args = argparser.parse_args(namespace=Args())

    frame = Frame.load_from_file(args.file)
    decoded = frame.decode()

    if args.output:
        with open(args.output, 'wb') as f:
            f.write(decoded)
        return

    # print to stdout
    if args.raw:
        sys.stdout.buffer.write(decoded)
    else:
        print(decoded)
