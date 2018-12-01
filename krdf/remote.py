import json
from krdf import KrdfError
from krdf.kcomp import FACT_FILES, RULE_FILES
import logging

def run_model(socket, model, args, facts=[], rules=[]):
    "start a model running on a worker thread"
    req = {
        "model": model.serialize(format="turtle").decode("utf-8"),
        "limit": args.limit,
        "plot": args.plot,
        "facts": facts,
        "rules": RULE_FILES
    }
    message = json.dumps(req)
    socket.send_string(message)

def collect_model(socket):
    "collect the result of the model run"
    result = socket.recv_string()

    data = json.loads(result)
    if "error" in data:
        logging.error("%s\n%s", data["error"], data["traceback"])
        raise KrdfError(data["error"])
    return data
