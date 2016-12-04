import os
import logging

from kappy.hybrid    import KappaRdf
from kappy.template  import Template
from kappy.merge     import merge
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

    @memoize("__template__")
    def template(self):
        _, _, t = get_one(self.__g, (self.__p, RBMC["template"], None))
        logging.info("processing part using template %s" % t)
        if self.templates is not None:
            t = os.path.join(self.templates, os.path.basename(t))
        return Template(t, self.templates, ns=self.namespace_manager)

    @memoize("__replacements__")
    def replacements(self):
        rep = {}
        for _, _, r in self.__g.triples((self.__p, RBMC["replace"], None)):
            _, _, tok = get_one(self.__g, (r, RBMC["string"], None))
            _, _, val = get_one(self.__g, (r, RBMC["value"], None))
            rep[tok] = val
        return rep

    @memoize("__data__")
    def data(self):
        template = self.template()
        logging.info("processing part using template %s", template.identifier)
        merged = merge(template)
        for tok, val in self.replacements().items():
            logging.info("replacing %s with %s" % (tok, val))
            merged = merged.replace(str(tok), str(val))
        return merged

    @memoize("__graph__")
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
