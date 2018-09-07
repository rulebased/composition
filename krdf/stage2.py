from rdflib.collection import Collection
from rdflib.term import Literal, URIRef
import logging

from krdf.namespace import RBMC, RBMO, RDF, SKOS
from krdf.utils import get_one, exists

def describe_operators(g, oplist):
    operators = []
    oplist = Collection(g, oplist)
    for desc in oplist:
        state = {}
        if exists(g, (desc, RDF["type"], RBMO["BoundState"])):
            state["bound"] = True
        elif exists(g, (desc, RDF["type"], RBMO["UnboundState"])):
            state["bound"] = False
        if exists(g, (desc, RBMO["stateOf"], None)):
            _, _, operator = get_one(g, (desc, RBMO["stateOf"], None))
            _, _, label = get_one(g, (operator, SKOS["prefLabel"], None))
            state["site"] = label.toPython()
        operators.append(state)
    return operators

def add_defaults(g, part):
    for _, _, kind in g.triples((URIRef(part["uri"]), RDF["type"], None)):
        for _, _, token in g.triples((kind, RBMC["tokens"], None)):
            try:
                _, _, label = get_one(g, (token, SKOS["prefLabel"], None))
            except Exception as e:
                logging.error("could not find label for %s" % token)
                raise
            if label.toPython() in part:
                continue
            if exists(g, (token, RBMC["default"], None)):
                _, _, default = get_one(g, (token, RBMC["default"], None))
                part[label.toPython()] = default.toPython()
    return part

def describe_part(g, parturi):
    """
    Emit a Python dictionary with a description of a single part,
    used by the second-stage compiler.
    """
    def literal(v):
        v = v.toPython()
        if isinstance(v, str):
            return v
        return b"%.16f" % v

    part = { "uri": parturi.toPython() }
    try:
        _, _, template = get_one(g, (parturi, RBMC["kappaTemplate"], None))
    except Exception as e:
        logging.error("%s could not find template" % (parturi,))
        raise e
    
    part["template"] = template.toPython()
    for _, _, replace in g.triples((parturi, RBMC["replace"], None)):
        try:
            _, _, token = get_one(g, (replace, RBMC["string"], None))
        except Exception as e:
            logging.error("%s could not find replacement token" % (parturi,))
            raise e

        try:
            _, _, value = get_one(g, (replace, RBMC["value"], None))
        except Exception as e:
            logging.error("%s could not find value for %s" % (parturi, token))
            raise

        if isinstance(value, Literal):
            part[token.toPython()] = literal(value)
            continue
        if exists(g, (value, SKOS["prefLabel"], None)):
            _, _, label = get_one(g, (value, SKOS["prefLabel"], None))
            part[token.toPython()] = label.toPython()
            continue

        ## if we are here, we are concerned with the states of operators
        data = {}
        replace = value
        _, _, value = get_one(g, (replace, RBMC["value"], None))
        data["value"] = literal(value)
        if exists(g, (replace, RBMC["upstream"], None)):
            _, _, oplist = get_one(g, (replace, RBMC["upstream"], None))
            data["upstream"] = list(reversed(describe_operators(g, oplist)))
        if exists(g, (replace, RBMC["downstream"], None)):
            _, _, oplist = get_one(g, (replace, RBMC["downstream"], None))
            data["downstream"] = describe_operators(g, oplist)

        data["upstream_size"] = len(data.get("upstream", []))
        data["downstream_size"] = len(data.get("downstream", []))
        data["context_size"] = data["upstream_size"] + data["downstream_size"] + 1

        part.setdefault(token.toPython(), []).append(data)

    return add_defaults(g, part)

def compile_stage2(ir, debug=False, **kw):
    """
    Translate the transitive closure of data, model under inference rules
    into a simple python dictionary that can be dealt with by Jinja2
    """
    logging.info("stage2: generating python representation")
    ir2 = {
        "circuits": []
    }

    model, _, _ = get_one(ir, (None, RDF["type"], RBMO["Model"]))

    _, _, prefix = get_one(ir, (model, RBMC["prefix"], None))
    ir2["prefix"] = prefix.toPython()

    for _, _, parts in ir.triples((model, RBMC["linear"], None)):
        circuit = list(map(lambda x: describe_part(ir, x), Collection(ir, parts)))
        ir2["circuits"].append({ "topology": "linear", "parts": circuit })

    for _, _, parts in ir.triples((model, RBMC["circular"], None)):
        circuit = list(map(lambda x: describe_part(ir, x), Collection(ir, parts)))
        ir2["circuits"].append({ "topology": "circular", "parts": circuit })

    logging.debug("="*80)
    logging.debug("stage2: output")
    logging.debug("-"*80)
    from pprint import pformat
    for line in pformat(ir2).split("\n"):
        logging.debug(line)
    logging.debug("="*80)

    return ir2
