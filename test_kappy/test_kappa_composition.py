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
        print self.frag.data()
        h = hashlib.sha256()
        h.update(self.frag.data())
        sha256 = h.hexdigest()
        assert sha256 == self.sha256

    def test_graph(self):
        if self.ask is None:
            return
        g = self.frag.graph()
        assert list(g.query(self.ask)) == [True]

    def test_ident(self):
        ident = str(self.frag.identifier)
        assert ident == self.ident

    def test_includes(self):
        ninc = len(self.frag.includes())
        assert ninc == self.includes

    def test_parts(self):
        npart = len(self.frag.parts())
        assert npart == self.parts

    def test_children(self):
        assert len(self.frag.children()) == self.includes + self.parts

class TestTopLevel(Fragment):
    def __init__(self):
        Fragment.__init__(
            self,
            KAPPA,
            "http://id.inf.ed.ac.uk/rbm/examples/sr#m",
            sha256 = "3d98aafb6d66038e8ba4168491b191c73a91e265aa4f7bbd17d560dbd9dd3fe8",
            ask = """
            PREFIX : <http://id.inf.ed.ac.uk/rbm/examples/sr#>
            PREFIX rbmo: <http://purl.org/rbm/rbmo#>
            ASK WHERE { :m a rbmo:Model }
            """,
            parts = 1
        )

class TestPspaRK(Fragment):
    def __init__(self):
        pspark = KAPPA.parts()[0]
        Fragment.__init__(
            self,
            pspark,
            "http://id.inf.ed.ac.uk/rbm/examples/sr#pspark"
        )

class TestPromoter(Fragment):
    def __init__(self):
        pspark = KAPPA.parts()[0]
        promoter = pspark.template()
        Fragment.__init__(
            self,
            promoter,
            "http://purl.org/rbm/templates/promoter.kappa",
            sha256 = "b922ab06398b2cfce63f70bc7dfb8f2b9c5b30c88e51998765c58d8008337a06",
            ask = """
            PREFIX rbmc: <http://purl.org/rbm/comp#>
            ASK WHERE { <http://purl.org/rbm/templates/promoter.kappa> a rbmc:Template }
            """,
            includes = 4
        )
