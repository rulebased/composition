import argparse
import logging
import os
import sys
from pkg_resources import resource_filename

import numpy as np
from scipy.stats.stats import pearsonr
from krdf.compiler import compile
from krdf.kcomp import FACT_FILES, RULE_FILES
from krdf.namespace import RDF, RBMO, GCC
from krdf.utils import Graph, get_one
from krdf.gen import gen_model, mutate_model, partname
from rdflib.collection import Collection
from concurrent.futures import ThreadPoolExecutor
import kappy

def name_model(g):
    m, _, _ = get_one(g, (None, RDF["type"], RBMO["Model"]))
    def parts():
        for _, _, pl in g.triples((m, GCC["linear"], None)):
            ps = Collection(g, pl)
            for p in ps:
                _, _, label = get_one(g, (p, GCC["part"], None))
                yield str(label)
        for _, _, pl in g.triples((m, GCC["circular"], None)):
            ps = Collection(g, pl)
            for p in ps:
                _, _, label = get_one(g, (p, GCC["part"], None))
                yield str(label)

    name = "_".join(parts())
    return name

def simulate(filename, args):
    client = kappy.KappaStd()
    client.set_default_sim_param(100, "[T] > 250000")
    client.add_model_file(filename)
    client.project_parse()
    client.simulation_start()
    client.wait_for_simulation_stop()
    data = client.simulation_plot(kappy.PlotLimit(points=10000))
    client.simulation_delete()
    return data

def score(results):
    LacI = np.array(list(x[1] for x in results["series"]))
    TetR = np.array(list(x[2] for x in results["series"]))
    LcI  = np.array(list(x[3] for x in results["series"]))

    r1, p1 = pearsonr(LacI, TetR)
    r2, p2 = pearsonr(TetR, LcI)
    r3, p3 = pearsonr(LcI, LacI)

    r = sum(0 if np.isnan(r) else r for r in (r1, r2, r3))
    p = max(-1 if np.isnan(p) else p for p in (p1, p2, p3))
    if p == -1: p = 1.0

    return (r, p)

def test_model(model, args, facts=[], rules=[]):
    modelname = name_model(model)
    mfilename = os.path.join(args.output, modelname + ".ttl")
    model.serialize(mfilename, format="ttl")

    program = compile(mfilename, facts=facts, rules=rules)

    kafilename = os.path.join(args.output, modelname + ".ka")
    fp = open(kafilename, "wb")
    fp.write(program)
    fp.close()

    logging.info("simulating %s" % modelname)
    def run(n):
        logging.info("starting [%d] %s" % (n, modelname))
        data = simulate(kafilename, args)
        logging.info("done [%d] %s" % (n, modelname))
        sc = score(data)
        logging.info("score %s %s" % (sc, modelname))
        return sc

    results = []
    with ThreadPoolExecutor() as executor:
        for result in executor.map(run, range(8)):
            results.append(result)

    sc = np.average(np.array(list(r[0] for r in results)))
    logging.info("average score %s %s" % (sc, modelname))
    return sc

def extract_circuit(model):
    mid, _, _ = get_one(model, (None, RDF["type"], RBMO["Model"]))
    if (mid, GCC["linear"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["linear"], None))
    elif (mid, GCC["circular"], None) in model:
        _, _, cid = get_one(model, (mid, GCC["circular"], None))
    circuit = []
    for part in Collection(model, cid):
        _, _, kind = get_one(model, (part, RDF["type"], None))
        circuit.append(kind)
    return circuit

def main():
    parser = argparse.ArgumentParser(description='Find an optimal genetic circuit')
    parser.add_argument('filename', type=str, help='Starting Circuit')
    parser.add_argument('database', type=str, help='Parts Database')
    parser.add_argument('output', type=str, help='Data Directory')
    parser.add_argument('debug', action="store_true", default=False, help='Turn on debugging')
    args = parser.parse_args()

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    model = Graph().parse(args.filename, format="turtle")
    database = Graph().parse(args.database, format="turtle")
    model += database
    circuit = extract_circuit(model)

    facts = FACT_FILES.copy()
    facts.append(args.database)

    seen = {}
    model, proto = gen_model(model, circuit, facts=facts, rules=RULE_FILES)
    seen[tuple(proto)] = test_model(model, args, facts=facts, rules=RULE_FILES)

    i = 0
    while i < 100:
        nmodel, nproto = mutate_model(model, proto, circuit, facts=facts, rules=RULE_FILES)
        if tuple(nproto) in seen:
            continue
        seen[tuple(nproto)] = test_model(nmodel, args, facts=facts, rules=RULE_FILES)
        if seen[tuple(nproto)] < seen[tuple(proto)]:
            model = nmodel
            proto = nproto
        i += 1
        
    def prettypart(part):
        _, _, label = get_one(database, (part, GCC["part"], None))
        return label

    results = sorted(seen.items(), key=lambda x: x[1])
    for proto, score in results:
        print("%.06f\t%s" % (score, " ".join(prettypart(p) for p in proto)))

if __name__ == '__main__':
    main()
