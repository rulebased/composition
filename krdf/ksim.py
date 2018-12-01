import argparse
import logging
import zmq
import json
import os
import traceback
import kappy
import tempfile
from krdf.compiler import compile
from concurrent.futures import ThreadPoolExecutor

def simulate(model, limit=100000, plot=100, facts=[], rules=[], **kw):
    try:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.file.write(bytes(model, "utf-8"))
        temp.file.close()

        program = compile(temp.name, facts=facts, rules=rules).decode("utf-8")

        client = kappy.KappaStd()
        client.set_default_sim_param(plot, "[T] > %d" % limit)
        client.add_model_string(program)
        client.project_parse()
        client.simulation_start()
        client.wait_for_simulation_stop()
        data = client.simulation_plot(kappy.PlotLimit(points=int(limit/plot)))
        data["kappa"] = program
        client.simulation_delete()
        return data
    finally:
        os.unlink(temp.name)

def handle_message(message, args):
    req = json.loads(message)
    req.setdefault("limit", 100000)
    req.setdefault("plot", 100)

    req.setdefault("facts", [])
    req.setdefault("rules", [])

    data = simulate(**req)
    return json.dumps(data)

def main():
    parser = argparse.ArgumentParser(description='Simulate a genetic circuit (0MQ Worker)')
    parser.add_argument('-t', '--threads', dest="threads", type=int, default=4, help='Number of simulation threads per circuit')
    parser.add_argument('-s', '--server', dest="server", default="tcp://localhost:9899", help="Work queue")
    parser.add_argument('-d', '--debug', dest="debug", default=False, action="store_true", help="Turn on debugging")
    args = parser.parse_args()

    if args.debug: loglevel=logging.DEBUG
    else: loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=loglevel)

    context = zmq.Context()

    def run(n):
        logging.info("[%d] connecting to server...", n)
        socket = context.socket(zmq.REP)
        socket.connect(args.server)
        while True:
            message = socket.recv()
            logging.info("[%d] simulating model...", n)
            try:
                reply = handle_message(message, args)
                logging.info("[%d] finished.", n)
                socket.send_string(reply)
            except Exception as e:
                exc = traceback.format_exc()
                logging.error("[%d] %s\n%s", n, e, exc)
                reply = json.dumps({"error": str(e), "traceback": exc})
                socket.send_string(reply)

    with ThreadPoolExecutor() as executor:
        executor.map(run, range(args.threads))
