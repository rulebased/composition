from kappy.namespace import PROV
from kappy.utils     import Graph

def merge(fragment):
    graph = merge_graph(fragment)
    kappa = merge_kappa(fragment)
    lines = []
    for line in graph.serialize(format="text/turtle").split("\n"):
        lines.append("#^ %s" % line)
    rdf = "\n".join(lines)
    return "\n".join((rdf, "\n", "#" * 80, "\n", kappa))

def merge_graph(fragment):
    g = Graph(identifier=fragment.identifier)
    g += fragment.graph()
    for c in fragment.transitive_children():
        g += c.graph()
    return g

def merge_kappa(fragment):
    k = fragment.kappa()
    k += "\n".join((c.kappa() for c in fragment.transitive_children()))
    return k
