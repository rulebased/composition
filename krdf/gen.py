import os
from krdf.namespace import RDF, RBMO, GCC
from krdf.utils import Graph, get_one, cbd
from rdflib import BNode, Literal, URIRef
from rdflib.collection import Collection
from random import choice
from string import ascii_letters

def get_random_part(model, circuit, kind):
    parts = list(p for p, _, _ in model.triples((None, RDF["type"], kind)))
    ### filter out already used parts
    parts = list(p for p in parts if p not in circuit)
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

def extract_circuit(model):
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
            circuit[i] = replace_part(model, circuit, i)
    return circuit

def replace_part(model, circuit, idx):
    """
    Replace the part in the model at the given index
    """
    part = circuit[idx]
    _, _, kind = get_one(model, (part, RDF["type"], None))
    sremove = list(model.triples((part, None, None)))
    oreplace = list(model.triples((None, None, part)))
    for triple in sremove:
        model.remove(triple)
    for triple in oreplace:
        model.remove(triple)
    pid_ = get_random_part(model, circuit, kind)
    pid = URIRef(pid_ + ascii_letters[idx])

    ## put in statements with renamed new part as subject
    ## and alpha-rename any blank nodes
    bnodes = {}
    for s, p, o in cbd(model, (pid_, None, None)):
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

def gen_model(model, facts=None, rules=[]):
    circuit = extract_circuit(model)
    proto = extract_proto(model)
    return (model, circuit)

def mutate_model(model, circuit, facts=None, rules=[]):
    nmodel = Graph()
    nmodel += model

    i = choice(range(len(circuit)))
    os.sys.stdout.buffer.write(model.serialize(format="turtle"))
    os.sys.stdout.buffer.flush()
    print(circuit[i])

    circuit[i] = replace_part(nmodel, circuit, i)
    return (nmodel, circuit)
