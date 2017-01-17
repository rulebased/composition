import argparse
import logging
import os
import sys
from pkg_resources import resource_filename

from kappy.kasim import parseString, KappaModel
from kappy.kasim.ast import Link

def main():
    parser = argparse.ArgumentParser(description='Produce a GraphViz dot file from a KaSim state dump')
    parser.add_argument('filename', type=str, help='Starting File')
    parser.add_argument('debug', action="store_true", default=False, help='Turn on debugging')
    args = parser.parse_args()

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    with open(args.filename, "r") as fp:
        data = fp.read().decode("utf-8")

    model = KappaModel(parseString(data))

    print "graph {"
    nodes = {}
    i = 0
    for v in model.init_values:
        sys.stderr.write("\n")
        print "    subgraph {"
        links = {}
        for pat in v.patterns:
            sys.stderr.write("%s\n" % pat)
            if "type" in pat.sites:
                kind = pat.sites["type"]
                name = "%s(%s)" % (pat.name, kind.state.text)
            else:
                name = pat.name
            print '        n%d[label="%s"];' % (i, name)
            for site in pat.sites.values():
                if not isinstance(site.link, Link):
                    continue
                links.setdefault(site.link.text, []).append(i)
            i += 1
        for (m, n) in links.values():
            print '        n%d -- n%d;' % (m, n)
        print "    }" ## ends subgraph
    print "}" ## ends graph

if __name__ == '__main__':
    main()
