import argparse
import time

from steg.steg import decode


class Args(argparse.Namespace):
    input: str
    output: str
    keep_images: bool
    fuzziness: int


def main():
    argparser = argparse.ArgumentParser(prog="decode_video")
    argparser.add_argument('input')
    argparser.add_argument('output')
    argparser.add_argument('--keep-images', '-k', default=False, action='store_true')
    argparser.add_argument('--fuzziness', '-f', default=17, type=int)


    args = argparser.parse_args(namespace=Args())

    start_time = time.time()

    with open(args.output, 'wb') as f:
        f.write(decode(args.input, keep_images=args.keep_images, fuzziness=args.fuzziness))

    print()
    print(f"took {time.time() - start_time}s")
