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
from rdflib.collection import Collection
from concurrent.futures import ThreadPoolExecutor
import kappy

def name_model(model):
    g = Graph().parse(model, format="turtle")
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
    client.set_default_sim_param(100, "[T] > 1000000")
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
    return (r1+r2+r3, max(p1, p2,p3))

def test_model(model, args):
    modelname = name_model(model)
    filename = os.path.join(args.output, modelname + ".ka")
    program = compile(model, facts=FACT_FILES, rules=RULE_FILES)
    fp = open(filename, "wb")
    fp.write(program)
    fp.close()

    logging.info("simulating %s" % modelname)
    def run(n):
        logging.info("starting [%d] %s" % (n, modelname))
        data = simulate(filename, args)
        logging.info("done [%d] %s" % (n, modelname))
        sc = score(data)
        logging.info("score %s %s" % (sc, modelname))
        return sc

    results = []
    with ThreadPoolExecutor() as executor:
        for result in executor.map(run, range(8)):
            print(result)
            results.append(result)

    sc = np.average(np.array(list(r[0] for r in results)))
    logging.info("average score %s %s" % (sc, modelname))
    return sc

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

    test_model(args.filename, args)

if __name__ == '__main__':
    main()
