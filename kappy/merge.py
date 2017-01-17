from kappy.utils import Graph

def kappa(doc):
    lines = []
    for line in doc.split(u"\n"):
        if line.startswith(u"#^ "):
            continue
        lines.append(line)
    return u"\n".join(lines)

def merge(model, docs):
    g = Graph().parse(model, format="turtle")
    k = []
    for doc in docs:
        g.parse(data=doc, format="application/x-kappa")
        k.append(kappa(doc))
    rdf = g.serialize(format="application/x-kappa")
    if isinstance(rdf, str):
        rdf = unicode(rdf, "utf-8")
    header = u"""
###
### This is an automatically generated simulation program derived from:
### %s
###

""" % (model,)

    return header + rdf + u"\n\n" + u"\n\n".join(k)


