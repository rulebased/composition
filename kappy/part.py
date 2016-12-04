import os
import logging

from kappy.hybrid    import KappaRdf
from kappy.template  import Template, TemplateError
from kappy.merge     import merge, merge_graph
from kappy.utils     import memoize, get_one
from kappy.namespace import RBMC

class Part(KappaRdf):
    def __init__(self, filename, templates, g, p, **kw):
        super(Part, self).__init__(filename, templates, ns=g.namespace_manager)
        self.__g = g
        self.__p = p

    @property
    def identifier(self):
        return self.filename

    def template(self):
        _, _, t = get_one(self.__g, (self.__p, RBMC["template"], None))
        logging.info("processing part using template %s" % t)
        if self.templates is not None:
            t = os.path.join(self.templates, os.path.basename(t))
        return Template(t, self.templates, ns=self.namespace_manager)

    def replacements(self):
        rep = {}
        for _, _, r in self.__g.triples((self.__p, RBMC["replace"], None)):
            _, _, tok = get_one(self.__g, (r, RBMC["string"], None))
            _, _, val = get_one(self.__g, (r, RBMC["value"], None))
            yield (tok, val)
            rep[tok] = val

        defined = list(rep.keys())
        for label, default in self.tokens():
            if label not in defined:
                if default is None:
                    err = "Required replacement %s not made and no default" % label
                    raise TemplateError(err)
                logging.info("using default for %s", label)
                yield (label, default)
                rep[label] = default

    def tokens(self):
        q = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rbmc: <http://purl.org/rbm/comp#>

        SELECT DISTINCT ?label ?default WHERE {
           ?template rbmc:tokens ?tok .
           ?tok rdfs:label ?label .
           OPTIONAL { ?tok rbmc:default ?default } .
        } ORDER BY ?label
        """
        merged = merge_graph(self.template())
        return merged.query(q)

    def data(self):
        template = self.template()
        logging.info("[%s] processing %s", id(self), self.identifier)
        logging.info("[%s] using template %s", id(self), template.identifier)
        merged = merge(template)
        for tok, val in self.replacements():
            logging.info("[%s] replacing '%s' with '%s'", id(self), str(tok), str(val))
            merged = merged.replace(str(tok), str(val))
        return merged

    def graph(self):
        g = KappaRdf.graph(self)
        remove = []
        ### find tokens that we have replaced
        for (_, _, tokdesc) in g.triples((None, RBMC["tokens"], None)):
            remove.append(tokdesc)
        for tokdesc in remove:
            g.remove((None, None, tokdesc))
            g.remove((tokdesc, None, None))
        return g
