import rdflib
from rdflib.collection import Collection
import argparse
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level = logging.INFO)
from string import join
import os
from itertools import chain

PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
RBMO = rdflib.Namespace("http://purl.org/rbm/rbmo#")
RBMC = rdflib.Namespace("http://purl.org/rbm/comp#")
RDF  = rdflib.RDF

def memoize(prop):
    def wrap(f):
        def run(self):
            if not hasattr(self, prop):
                setattr(self, prop, f(self))
            return getattr(self, prop)
        return run
    return wrap

class KappaRdf(object):
    def __init__(self, filename, templates):
        self.filename = filename
        self.templates = templates

    @property
    @memoize('__data__')
    def data(self):
        logging.info("reading and parsing %s..." % self.filename)
        with open(self.filename) as fp:
            return fp.read()

    @property
    @memoize('__graph__')
    def graph(self):
        rdf_lines = []
        for line in self.data.split("\n"):
            if line.startswith("#^ "):
                rdf_lines.append(line[3:])
        g = rdflib.Graph()
        g.parse(
            data     = join(rdf_lines, "\n"),
            format   = "text/turtle",
            location = self.filename
        )
        return g

    @property
    @memoize('__kappa__')
    def kappa(self):
        g = rdflib.Graph()
        kappa_lines = []
        for line in self.data.split("\n"):
            if not line.startswith("#^ "):
                kappa_lines.append(line)
        data = "##\n## %s\n##\n\n" % g.absolutize(self.filename)
        data += join(kappa_lines, "\n")
        data += "\n\n"
        return data

    def includes(self):
        q = """
        PREFIX rbmc: <http://purl.org/rbm/comp#>

        SELECT DISTINCT ?template WHERE {
            ?model rbmc:include ?template
        }
        """
        return [t[0] for t in self.graph.query(q)]

    @property
    @memoize("__children__")
    def children(self):
        children = []
        for template in self.includes():
            if self.templates is not None:
                template = os.path.join(self.templates, os.path.basename(template))
            children.append(KappaRdf(template, self.templates))
        return children + self.parts

    @property
    def identifier(self):
        classes = [RBMO["Model"], RBMO["Kappa"], RBMC["Template"]]
        queries = [self.graph.triples((None, RDF["type"], c)) for c in classes]
        triples = list(chain(*queries))
        if len(triples) == 0:
            logging.error("RDF graph in %s does not contain an RBM class" % self.filename)
            raise Exception("RDF graph in %s does not contain an RBM class" % self.filename)
        if len(triples) > 1:
            logging.warning("RDF graph in %s contains too many RBM classes:\n%s" % (self.filename, "\n".join("%s\t%s" % (t[0], t[2]) for t in triples)))
        return triples[0][0]

    @property
    def merged_graph(self):
        g = rdflib.Graph(identifier = self.identifier)
        g += self.graph
        for c in self.children:
            g.add((self.identifier, PROV["derivesFrom"], c.identifier))
            g += c.merged_graph
        return g

    @property
    def merged_kappa(self):
        d = self.kappa
        d += join((c.merged_kappa for c in self.children), "\n")
        return d

    @property
    def merged(self):
        rdflines = []
        for line in self.merged_graph.serialize(format="text/turtle").split("\n"):
            rdflines.append("#^ %s" % line)
        rdf_section = join(rdflines, "\n")
        kappa_section = self.merged_kappa
        return join((rdf_section, "\n", "#" * 80, "\n", kappa_section), "\n")

    @property
    @memoize("__parts__")
    def parts(self):
        plist = []
        q = (self.identifier, RBMC["parts"], None)
        for _, _, o in self.graph.triples(q):
            l = Collection(self.graph, o)
            for p in l:
                plist.append(Part(self.identifier, self.templates, self.graph, p))
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
        super(Part, self).__init__(filename, templates)
        self.__g = g
        self.__p = p

    @property
    def identifier(self):
        return self.filename

    @property
    @memoize("__data__")
    def data(self):
        _,_,t = get_one(self.__g, (self.__p, RBMC["template"], None))
        logging.info("processing part using template %s" % t)
        if self.templates is not None:
            t = os.path.join(self.templates, os.path.basename(t))
        kr = KappaRdf(t, self.templates)
        merged = kr.merged
        for _,_,r in self.__g.triples((self.__p, RBMC["replace"], None)):
            _,_,tok = get_one(self.__g, (r, RBMC["token"], None))
            _,_,val = get_one(self.__g, (r, RBMC["value"], None))
            logging.info("replacing %s with %s" % (tok, val))
            merged = merged.replace(str(tok), str(val))
        return merged

if __name__ == '__main__':
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
