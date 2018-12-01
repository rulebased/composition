import argparse
import logging
import os
import sys
import zmq
import json
from queue import Queue

import numpy as np
from numpy.random import exponential
from math import ceil
from scipy.stats.stats import pearsonr
from krdf.kcomp import FACT_FILES, RULE_FILES
from krdf.namespace import RDF, RBMO, GCC
from krdf.utils import Graph, get_one, cbd
from krdf.gen import gen_model, mutate_model
from krdf.remote import run_model, collect_model
from krdf import KrdfError
from rdflib.collection import Collection

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


def score_min(results):
    LacI = np.array(list(x[1] for x in results["series"]))
    TetR = np.array(list(x[2] for x in results["series"]))
    LcI  = np.array(list(x[3] for x in results["series"]))

    r1, _ = pearsonr(LacI, TetR)
    r2, _ = pearsonr(TetR, LcI)
    r3, _ = pearsonr(LcI, LacI)

    r = min(0 if np.isnan(r) else r for r in (r1, r2, r3))

    return -1 * r

def score_sum(results):
    LacI = np.array(list(x[1] for x in results["series"]))
    TetR = np.array(list(x[2] for x in results["series"]))
    LcI  = np.array(list(x[3] for x in results["series"]))

    r1, _ = pearsonr(LacI, TetR)
    r2, _ = pearsonr(TetR, LcI)
    r3, _ = pearsonr(LcI, LacI)

    r = sum(0 if np.isnan(r) else r for r in (r1, r2, r3))

    return -1 * r

def test_models(context, score, models, args, facts=[], rules=[]):
    "start simulations of a list of models, and coalesce the results"
    q = Queue()
    for name in models:
        socket = context.socket(zmq.REQ)
        socket.connect(args.server)
        q.put((name, socket))
        run_model(socket, models[name], args, facts, rules)

    scores = {}
    while not q.empty():
        name, socket = q.get()
        try:
            data = collect_model(socket)
        except KrdfError as e:
            ## try again, mysterious unreproducable parse error
            q.put((name, socket))
            run_model(socket, models[name], args, facts, rules)
            continue
        socket.close()

        kappa = os.path.join(args.output, name + ".ka")
        with open(kappa, "w") as fp:
            fp.write(data["kappa"])

        a = np.array(data["series"])
        csv = os.path.join(args.output, name + ".csv")
        np.savetxt(csv, a, delimiter=',')

        scores[name] = score(data)
        logging.info("%f %s", scores[name], name)

        sc = os.path.join(args.output, name + ".score")
        with open(sc, "w") as fp:
            fp.write("%s\n" % scores[name])

    return scores

def topn(scores, n):
    "return the items with the top n scores"
    top = list(i[0] for i in sorted(scores.items(), key=lambda a: a[1]) if not np.isnan(i[1]))
    top.reverse()
    return top[:n]

def main():
    parser = argparse.ArgumentParser(description='Find an optimal genetic circuit')
    parser.add_argument('-l', '--limit', dest='limit', type=int, default=100000, help='Simulation step limit')
    parser.add_argument('-p', '--plot', dest='plot', type=int, default=100, help='Plot every N points')
    parser.add_argument('-o', '--population', dest='population', type=int, default=20, help='Population size to simulate')
    parser.add_argument('-e', '--selection', dest='selection', type=int, default=4, help='Selection from the population')
    parser.add_argument('-m', '--mutation', dest='mutation', type=float, default=0.5, help='Mutation rate per offspring')
    parser.add_argument('-g', '--generations', dest='generations', type=int, default=10, help='Number of generations')
    parser.add_argument('-s', '--server', dest="server", default="tcp://localhost:9898", help="Server side of queue")    
    parser.add_argument('-f', '--fitness', dest="fitness", default="min", help="Fitness function: min for best pair-wise anti-correlation, sum for best global anti-correlation")
    parser.add_argument('filename', type=str, help='Starting Circuit')
    parser.add_argument('database', type=str, help='Parts Database')
    parser.add_argument('output', type=str, help='Data Directory')
    parser.add_argument('debug', action="store_true", default=False, help='Turn on debugging')
    args = parser.parse_args()

    if args.fitness == "min":
        score = score_min
    elif args.fitness == "sum":
        score = score_sum
    else:
        raise KrdfError("unknown fitness function: %s" % args.score)

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    context = zmq.Context()

    model = Graph().parse(args.filename, format="turtle")
    database = Graph().parse(args.database, format="turtle")

    facts = FACT_FILES.copy()
    facts.append(args.database)

    model, circuit = gen_model(model, database)

    name = name_model(model)
    models = { name: model }
    circuits = { name: circuit }
    scores = test_models(context, score, {name: model}, args, facts=facts, rules=RULE_FILES)

    for _ in range(args.generations):
        top = topn(scores, args.selection)
        population = {}
        for parent in top:
            logging.info("mutating %s", parent.replace("_", " "))

            model = models[parent]
            circuit = circuits[parent]

            children = int(args.population / len(top))
            for _ in range(children):
                rnd = exponential(args.mutation)
                nmodel, ncircuit = model, circuit
                for _ in range(int(ceil(rnd))):
                    nmodel, ncircuit = mutate_model(nmodel, ncircuit, database)
                child = name_model(nmodel)
                if child in models:
                    continue
                logging.info("  --> (%d) %s", ceil(rnd), child.replace("_", " "))
                models[child] = nmodel
                circuits[child] = ncircuit
                population[child] = nmodel

                turtle = os.path.join(args.output, child + ".ttl")
                models[child].serialize(turtle, format="turtle")

        results = test_models(context, score, population, args, facts=facts, rules=RULE_FILES)
        scores.update(results)

        for circuit in population:
            turtle = os.path.join(args.output, circuit + ".ttl")
            models[circuit].serialize(turtle, format="turtle")



    top = topn(scores, args.selection)
    for circuit in top:
        print("%.06f\t%s" % (scores[circuit], circuit.replace("_", " ")))

if __name__ == '__main__':
    main()
