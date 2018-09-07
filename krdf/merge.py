from krdf.utils import Graph

def kappa(doc):
    if isinstance(doc, str):
        doc = bytes(doc, "utf-8")
    lines = []
    for line in doc.split(b"\n"):
        if line.startswith(b"#^ "):
            continue
        lines.append(line)
    return b"\n".join(lines)

def merge(model, docs):
    g = Graph().parse(model, format="turtle")
    k = []
    for doc in docs:
        g.parse(data=doc, format="application/x-kappa")
        k.append(kappa(doc))
    rdf = g.serialize(format="application/x-kappa")
    if isinstance(rdf, str):
        rdf = unicode(rdf, "utf-8")
    header = b"""
###
### This is an automatically generated simulation program derived from:
### %s
###

""" % (bytes(model, "utf-8"),)

    return header + rdf + b"\n\n" + b"\n\n".join(k)


