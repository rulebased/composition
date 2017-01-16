from kappy.namespace import RDF, RBMC, RBMO
from kappy.utils import get_one
from rdflib.parser import create_input_source
import logging

def compile_stage5(g, docs, **kw):
    """
    Derive initialisation for genetic circuits present
    in the model
    """
    model, _, _ = get_one(g, (None, RDF["type"], RBMO["Model"]))
    for _, _, inc in g.triples((model, RBMC["include"], None)):
        logging.info("stage5: including %s" % inc)
        fp = create_input_source(inc.toPython()).getByteStream()
        doc = fp.read()
        fp.close()
        docs.insert(0, doc)
    return docs
