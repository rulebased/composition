import argparse
import logging
import os

from kappy.hybrid import KappaRdf
from kappy.merge  import merge

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description='Test extract RDF from a Kappa/RDF file')
    parser.add_argument('filename', type=str,
                        help='Starting File')
    parser.add_argument('--templates', type=str, default=None,
                        help='Template prefix')
    parser.add_argument('--tokens', default=False,
                        action="store_true", help='Output expected tokens')
    args = parser.parse_args()
    kr = KappaRdf(args.filename, args.templates)
    if args.tokens:
        print " ".join(kr.tokens)
    else:
        print merge(kr)


if __name__ == '__main__':
    main()
