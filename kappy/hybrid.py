import os
import logging
from itertools import chain
from kappy.utils import Graph, memoize
from kappy.namespace import RBMO, RBMC, RDF
from rdflib.collection import Collection

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

    def data(self):
        #logging.info("reading and parsing %s..." % self.filename)
        with open(self.filename) as fp:
            return fp.read()

    def graph(self):
        ## first try to parse as plain turtle
        g = Graph()
        try:
            g.parse(data=self.data(), format="text/turtle", publicID=self.location)
            if len(g) > 0:
                self.__embedded = False
                return g
        except:
            pass

        ## ok, that didn't work or we got no triples so look for embedded kappa
        g = Graph()
        g.parse(data=self.data(), format="application/x-kappa", publicID=self.location)
        return g

    def kappa(self):
        if self.__embedded is False:
            return ""
        g = Graph()
        kappa_lines = []
        for line in self.data().split("\n"):
            if not line.startswith("#^ "):
                kappa_lines.append(line)
        data = "##\n## %s\n##\n" % g.absolutize(self.filename)
        data += "\n".join(kappa_lines)
        data += "\n\n"
        return data

    @property
    @memoize("__identifier__")
    def identifier(self):
        classes = [RBMO["Model"], RBMO["Kappa"], RBMC["Template"]]
        queries = [self.graph().triples((None, RDF["type"], c)) for c in classes]
        triples = list(chain(*queries))
        if len(triples) == 0:
            logging.error("RDF graph in %s does not contain an RBM class" % self.filename)
            print self.graph().serialize(format="turtle")
            raise Exception("RDF graph in %s does not contain an RBM class" % self.filename)
        if len(triples) > 1:
            classes = "\n".join("%s\t%s" % (t[0], t[2]) for t in triples)
            logging.warning("RDF graph in %s contains too many RBM classes:\n%s" % (self.filename, classes))
        ident = triples[0][0]
        logging.info("Model identifier is %s" % ident)
        return ident

    def includes(self):
        q = """
        PREFIX rbmc: <http://purl.org/rbm/comp#>

        SELECT DISTINCT ?template WHERE {
            %s rbmc:include ?template
        }
        """ % self.identifier.n3()
        return list(t[0] for t in self.graph().query(q))

    def children(self):
        children = []
        for template in self.includes():
            if self.templates is not None:
                template = os.path.join(self.templates, os.path.basename(template))
            from kappy.template import Template # XXX Bad style
            child = Template(template, self.templates, ns=self.namespace_manager, location=self.location)
            children.append(child)
            logging.debug("%s has child %s", self.identifier, child.identifier)
        children = children + self.parts()
        return children

    def transitive_children(self):
        for c in self.children():
            yield c
            for cc in c.children():
                yield c

    def parts(self):
        from kappy.part import Part # XXX Bad style
        logging.info("looking for the parts of %s" % self.identifier)
        plist = []
        g = self.graph()
        q = (self.identifier, RBMC["parts"], None)
        for _, _, o in g.triples(q):
            l = Collection(g, o)
            for p in l:
                logging.info("found part %s" % p)
                plist.append(Part(p, self.templates, g, p))
        return plist
