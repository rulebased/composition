from kappy.utils import Graph

def kappa(doc):
    lines = []
    for line in doc.split("\n"):
        if line.startswith("#^ "):
            continue
        lines.append(line)
    return "\n".join(lines)

def merge(model, docs):
    g = Graph().parse(model, format="turtle")
    k = []
    for doc in docs:
        g.parse(data=doc, format="application/x-kappa")
        k.append(kappa(doc))
    rdf = g.serialize(format="application/x-kappa")
    return rdf + "\n\n" + "\n\n".join(k)


