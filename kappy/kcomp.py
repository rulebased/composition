import argparse
import logging
import os
import sys
from pkg_resources import resource_filename

from kappy.compiler import compile

FACT_FILES = map(lambda x: resource_filename("kappy", "rdf/%s" % x), [
    "composition.ttl"
])

RULE_FILES = map(lambda x: resource_filename("kappy", "rdf/%s" % x), [
    "rdfs-rules.n3",
    "composition.n3"
])

def main():
    parser = argparse.ArgumentParser(description='Test extract RDF from a Kappa/RDF file')
    parser.add_argument('filename', type=str, help='Starting File')
    parser.add_argument('debug', action="store_true", default=False, help='Turn on debugging')
    args = parser.parse_args()

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    data = compile(args.filename, facts=FACT_FILES, rules=RULE_FILES)
    print data

if __name__ == '__main__':
    main()
