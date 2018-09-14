from krdf.kasim import parseString, KappaModel
from krdf.utils import Graph
import logging

def check_rdf_syntax(doc):
    Graph().parse(data=doc, format="application/x-kappa")
    
def check_kappa_rules(doc):
    ast = parseString(doc)
    model = KappaModel(ast)
    for statement in ast:
        logging.debug(statement)

