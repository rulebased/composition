import kappy
from rdflib import Graph

def test_parse_rdf_in_kappa():
    data = "#^ @prefix : <http://example.org/>.\n#^ :a :b :c.\n"
    g = Graph()
    g.parse(data=data, format="krdf")
    assert len(g) == 1
