import os
from krdf.namespace import RDF, RBMO, GCC
from krdf.utils import Graph, get_one, cbd, dump_graph, exists
from rdflib import BNode, Literal, URIRef
from rdflib.collection import Collection
from random import choice
from string import ascii_letters
import logging

def get_random_part(database, kind):
    parts = list(p for p, _, _ in database.triples((None, RDF["type"], kind)))
    return choice(parts)

def extract_proto(model):
    """
    Extract circuit prototype -- the list of part types that make up the circuit
    """
    mid, _, _ = get_one(model, (None, RDF["type"], RBMO["Model"]))
    if (mid, GCC["linear"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["linear"], None))
    elif (mid, GCC["circular"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["circular"], None))
    proto = []
    for part in Collection(model, cid):
        _, _, kind = get_one(model, (part, RDF["type"], None))
        proto.append(kind)
    return proto

def extract_circuit(model, database):
    """
    Extract the list of parts that make up the circuit, filling in any that
    are identified with blank nodes randomly.
    """
    mid, _, _ = get_one(model, (None, RDF["type"], RBMO["Model"]))
    if (mid, GCC["linear"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["linear"], None))
    elif (mid, GCC["circular"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["circular"], None))

    circuit = list(Collection(model, cid))
    for i in range(len(circuit)):
        part = circuit[i]
        if isinstance(part, BNode):
            circuit[i] = replace_part(model, circuit, i, database)
    return circuit

def replace_part(model, circuit, idx, database):
    """
    Replace the part in the model at the given index
    """
    part = circuit[idx]
    #dump_graph(model)
    _, _, kind = get_one(model, (part, RDF["type"], None))
    sremove = list(model.triples((part, None, None)))
    oreplace = list(model.triples((None, None, part)))
    for triple in sremove:
        model.remove(triple)
    for triple in oreplace:
        model.remove(triple)
    pid_ = get_random_part(database, kind)
    pid = URIRef(pid_ + ascii_letters[idx])

    ## put in statements with renamed new part as subject
    ## and alpha-rename any blank nodes
    bnodes = {}
    for s, p, o in cbd(database, (pid_, None, None)):
        if s == pid_: s = pid
        elif isinstance(s, BNode):
            if s not in bnodes:
                bnodes[s] = BNode()
            s = bnodes[s]
        if p == GCC["part"]:
            o = Literal(o + ascii_letters[idx])
        elif p == RBMO["stateOf"]:
            ### fix to support multi-operators
            o = circuit[idx-1]
        if isinstance(o, BNode):
            if o not in bnodes:
                bnodes[o] = BNode()
            o = bnodes[o]
        model.add((s, p, o))
    ## link in to statements referring to old part
    for s, p, _ in oreplace:
        model.add((s, p, pid))
    return pid

def gen_model(model, database):
    circuit = extract_circuit(model, database)
    proto = extract_proto(model)
    ## the "next" linkage for RBS needs to be fixed up in the model.
    for i in range(len(circuit)):
        part = circuit[i]
        if exists(model, (part, GCC["next"], None)):
            _, _, next = get_one(model, (part, GCC["next"], None))
            _, _, label = get_one(model, (circuit[i+1], GCC["part"], None))
            model.remove((part, GCC["next"], next))
            model.add((part, GCC["next"], label))
    return (model, circuit)

def mutate_model(model, circuit, database):
    logging.info("mutate: circuit is %s", circuit)
    nmodel = Graph()
    nmodel += model

    i = choice(range(len(circuit)))
    logging.info("mutate: replacing part %d: %s", i, circuit[i])

    try:
        part = replace_part(nmodel, circuit, i, database)
    except Exception as e:
        dump_graph(model)
        raise e
    ncircuit = circuit.copy()
    ncircuit[i] = part

    ## fixup the "next" linkage for RBS
    if exists(model, (part, GCC["next"], None)):
        _, _, next = get_one(model, (part, GCC["next"], None))
        _, _, label = get_one(model, (circuit[i+1], GCC["part"], None))
        model.remove((part, GCC["next"], next))
        model.add((part, GCC["next"], label))

    logging.info("mutate: repacement part is %s", circuit[i])
    return (nmodel, ncircuit)
