from krdf.namespace import RBMT
from krdf.utils import Graph, get_template
import logging

def compile_stage6(model, docs, **kw):
    """
    Derive initialisation for genetic circuits present
    in the model
    """
    logging.info("stage6: initialising circuits")
    circuits = []
    for circuit in model["circuits"]:
        parts = circuit["parts"]
        init = []
        for i in range(len(parts)):
            part = "DNA(type{" + parts[i]["name"] + "}"
            if i == 0 and circuit["topology"] == "circular":
                part += ", us[%d]" % (len(parts) - 1)
            elif i > 0:
                part += ", us[%d]" % (i - 1)
            if i == len(parts) - 1 and circuit["topology"] == "circular":
                part += ", ds[%d]" % (len(parts) - 1)
            elif i < len(parts) - 1:
                part += ", ds[%d]" % i
            part += ")"
            init.append(part)
        circuits.append(", ".join(init))

    t = get_template(RBMT["init.ka"])
    docs.insert(0, t.render(circuits = circuits))
    return docs
