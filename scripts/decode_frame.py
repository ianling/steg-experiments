import argparse
from steg.frame import Frame


class Args(argparse.Namespace):
    file: str


def main():
    argparser = argparse.ArgumentParser(prog="decode_frame")
    argparser.add_argument('file')
    args = argparser.parse_args(namespace=Args())

    frame = Frame.load_from_file(args.file)

    print(frame.decode())



