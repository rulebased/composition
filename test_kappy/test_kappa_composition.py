from kappy import KappaRdf
import os.path as p
import hashlib
import logging

MODULAR = p.join(p.dirname(__file__), "..", "modular")
TEMPLATES = p.join(MODULAR, "templates")
EXAMPLE = p.join(MODULAR, "sr.ttl")

KAPPA = KappaRdf(EXAMPLE, TEMPLATES)

class Fragment(object):
    def __init__(self, frag, ident, sha256=None, ask=None,
                 includes=0, parts=0):
        self.frag     = frag
        self.ident    = ident
        self.sha256   = sha256
        self.ask      = ask
        self.includes = includes
        self.parts    = parts

    def test_data(self):
        if self.sha256 is None:
            return
        print self.frag.data
        h = hashlib.sha256()
        h.update(self.frag.data)
        sha256 = h.hexdigest()
        assert sha256 == self.sha256

    def test_graph(self):
        if self.ask is None:
            return
        g = self.frag.graph
        assert list(g.query(self.ask)) == [True]

    def test_ident(self):
        ident = str(self.frag.identifier)
        assert ident == self.ident

    def test_includes(self):
        ninc = len(self.frag.includes)
        assert ninc == self.includes

    def test_parts(self):
        npart = len(self.frag.parts)
        assert npart == self.parts

    def test_children(self):
        assert len(self.frag.children) == self.includes + self.parts
        
class TestTopLevel(Fragment):
    def __init__(self):
        Fragment.__init__(
            self,
            KAPPA,
            "http://id.inf.ed.ac.uk/rbm/examples/sr#m",
            sha256 = "60b171ba682eac6f427c84a1fad7682c5902cefa417608748c3ce7de8fc722d8",
            ask = """
            PREFIX : <http://id.inf.ed.ac.uk/rbm/examples/sr#>
            PREFIX rbmo: <http://purl.org/rbm/rbmo#>
            ASK WHERE { :m a rbmo:Model }
            """,
            parts = 1
        )

class TestPspaRK(Fragment):
    def __init__(self):
        pspark = KAPPA.parts[0]
        Fragment.__init__(
            self,
            pspark,
            "http://id.inf.ed.ac.uk/rbm/examples/sr#pspark",
            includes = 4
        )
