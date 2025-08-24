import argparse
from steg.frame import Frame
from steg.util import fuzzy_equals


class Args(argparse.Namespace):
    file1: str
    file2: str
    fuzziness: int


def main():
    argparser = argparse.ArgumentParser(prog="comparer")
    argparser.add_argument('file1')
    argparser.add_argument('file2')
    argparser.add_argument('--fuzziness', '-f', default=17, type=int)
    args = argparser.parse_args(namespace=Args())

    frame1 = Frame.load_from_file(args.file1)
    frame2 = Frame.load_from_file(args.file2)

    decoded1 = frame1.decode()
    decoded2 = frame2.decode()

    if decoded1 != decoded2:
        print("ERROR: decoded bytes not equal")

    index = 0
    for tile1, tile2 in zip(frame1.tiles(), frame2.tiles()):
        if not fuzzy_equals(tile1, tile2, fuzziness=args.fuzziness):
            print(f"{index}: {tile1} != {tile2}")

        index += 1



