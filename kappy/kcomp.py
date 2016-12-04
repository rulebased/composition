import argparse
import logging
import os
from itertools import chain
from utils import memoize, Graph

import rdflib
from rdflib.collection import Collection

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
RBMO = rdflib.Namespace("http://purl.org/rbm/rbmo#")
RBMC = rdflib.Namespace("http://purl.org/rbm/comp#")
RDF = rdflib.RDF




class KappaRdf(object):
    def __init__(self, filename, templates, ns = None, location = None):
        self.filename = filename
        self.templates = templates
        self.__embedded = True
        self.namespace_manager = ns
        if location is None:
            self.location = self.filename
        else:
            self.location = location

    @property
    @memoize('__data__')
    def data(self):
        logging.info("reading and parsing %s..." % self.filename)
        with open(self.filename) as fp:
            return fp.read()

    @property
    @memoize('__graph__')
    def graph(self):
        ## first try to parse as plain turtle
        g = Graph()
        try:
            g.parse(data=self.data, format="text/turtle", publicID=self.location)
            if len(g) > 0:
                self.__embedded = False
                return g
        except:
            pass

        ## ok, that didn't work or we got no triples so look for embedded kappa
        g = Graph()
        g.parse(data=self.data, format="application/x-kappa", publicID=self.location)
        return g

    @property
    @memoize('__kappa__')
    def kappa(self):
        if self.__embedded is False:
            return ""
        g = Graph()
        kappa_lines = []
        for line in self.data.split("\n"):
            if not line.startswith("#^ "):
                kappa_lines.append(line)
        data = "##\n## %s\n##\n\n" % g.absolutize(self.filename)
        data += "\n".join(kappa_lines)
        data += "\n\n"
        return data

    @property
    @memoize("__includes__")
    def includes(self):
        q = """
        PREFIX rbmc: <http://purl.org/rbm/comp#>

        SELECT DISTINCT ?template WHERE {
            ?model rbmc:include ?template
        }
        """
        return list(t[0] for t in self.graph.query(q))

    @property
    @memoize("__children__")
    def children(self):
        logging.debug("finding children of %s" % self.identifier)
        children = []
        for template in self.includes:
            if self.templates is not None:
                template = os.path.join(self.templates, os.path.basename(template))
            child = KappaRdf(template, self.templates, ns=self.namespace_manager, location=self.location)
            children.append(child)
            logging.debug("%s has child %s", self.identifier, child.identifier)
        children = children + self.parts
        return children

    @property
    @memoize("__identifier__")
    def identifier(self):
        classes = [RBMO["Model"], RBMO["Kappa"], RBMC["Template"]]
        queries = [self.graph.triples((None, RDF["type"], c)) for c in classes]
        triples = list(chain(*queries))
        if len(triples) == 0:
            logging.error("RDF graph in %s does not contain an RBM class" % self.filename)
            print self.graph.serialize(format="turtle")
            raise Exception("RDF graph in %s does not contain an RBM class" % self.filename)
        if len(triples) > 1:
            classes = "\n".join("%s\t%s" % (t[0], t[2]) for t in triples)
            logging.warning("RDF graph in %s contains too many RBM classes:\n%s" % (self.filename, classes))
        ident = triples[0][0]
        logging.info("Model identifier is %s" % ident)
        return ident

    @property
    def merged_graph(self):
        g = Graph(identifier=self.identifier)
        g += self.graph
        for c in self.children:
            g.add((self.identifier, PROV["derivesFrom"], c.identifier))
            g += c.merged_graph
        return g

    @property
    def merged_kappa(self):
        d = self.kappa
        d += "\n".join((c.merged_kappa for c in self.children))
        return d

    @property
    def merged(self):
        rdflines = []
        for line in self.merged_graph.serialize(format="text/turtle").split("\n"):
            rdflines.append("#^ %s" % line)
        rdf_section = "\n".join(rdflines)
        kappa_section = self.merged_kappa
        return "\n".join((rdf_section, "\n", "#" * 80, "\n", kappa_section))

    @property
    @memoize("__parts__")
    def parts(self):
        logging.info("looking for the parts of %s" % self.identifier)
        plist = []
        q = (self.identifier, RBMC["parts"], None)
        for _, _, o in self.graph.triples(q):
            l = Collection(self.graph, o)
            for p in l:
                logging.info("found part %s" % p)
                plist.append(Part(p, self.templates, self.graph, p))
        return plist

    @property
    @memoize("__tokens__")
    def tokens(self):
        q = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rbmc: <http://purl.org/rbm/comp#>

        SELECT DISTINCT ?label WHERE {
            [ rbmc:tokens [ rdfs:label ?label ] ]
        } ORDER BY ?label
        """
        return [row[0] for row in self.merged_graph.query(q)]


def get_one(g, t):
    triples = list(g.triples(t))
    if len(triples) == 0:
        logging.error("get_one returned no triples")
        return
    if len(triples) > 1:
        logging.error("get_one returned more than one triple")
        return
    return triples[0]


class Part(KappaRdf):
    def __init__(self, filename, templates, g, p):
        super(Part, self).__init__(filename, templates, ns=g.namespace_manager)
        self.__g = g
        self.__p = p

    @property
    def identifier(self):
        return self.filename

    @property
    @memoize("__data__")
    def data(self):
        _, _, t = get_one(self.__g, (self.__p, RBMC["template"], None))
        logging.info("processing part using template %s" % t)
        if self.templates is not None:
            t = os.path.join(self.templates, os.path.basename(t))
        kr = KappaRdf(t, self.templates, ns=self.namespace_manager)
        merged = kr.merged
        for _, _, r in self.__g.triples((self.__p, RBMC["replace"], None)):
            _, _, tok = get_one(self.__g, (r, RBMC["string"], None))
            _, _, val = get_one(self.__g, (r, RBMC["value"], None))
            logging.info("replacing %s with %s" % (tok, val))
            merged = merged.replace(str(tok), str(val))
        return merged


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
        print kr.merged


if __name__ == '__main__':
    main()
