import argparse
import logging
import os
import sys
import zmq
import json

import numpy as np
from scipy.stats.stats import pearsonr
from krdf.kcomp import FACT_FILES, RULE_FILES
from krdf.namespace import RDF, RBMO, GCC
from krdf.utils import Graph, get_one, cbd
from krdf.remote import run_model, collect_model

def main():
    parser = argparse.ArgumentParser(description='Find an optimal genetic circuit')
    parser.add_argument('-l', '--limit', dest='limit', type=int, default=100000, help='Simulation step limit')
    parser.add_argument('-p', '--plot', dest='plot', type=int, default=100, help='Plot every N points')
    parser.add_argument('-s', '--server', dest="server", default="tcp://localhost:9898", help="Server side of queue")
    parser.add_argument('debug', action="store_true", default=False, help='Turn on debugging')

    parser.add_argument('filename', type=str, help='Starting Circuit')
    parser.add_argument('auxfiles', nargs="*", default=[], help='Parts Database')
    args = parser.parse_args()

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    context = zmq.Context()

    model = Graph().parse(args.filename, format="turtle")

    facts = FACT_FILES.copy()
    facts.extend(args.auxfiles)

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(args.server)
    logging.info("requesting model to run...")
    run_model(socket, model, args, facts, RULE_FILES)
    logging.info("waiting for result...")
    data = collect_model(socket)
    logging.info("done.")
    socket.close()
    context.destroy()

if __name__ == '__main__':
    main()
