from kappy.namespace import RBMT
from kappy.utils import Graph, get_template

def compile_stage5(model, docs, **kw):
    """
    Derive initialisation for genetic circuits present
    in the model
    """
    circuits = []
    for circuit in model["circuits"]:
        parts = circuit["parts"]
        init = []
        for i in range(len(parts)):
            part = "DNA(type~" + parts[i]["name"]
            if i == 0 and circuit["topology"] == "circular":
                part += ", us!%d" % (len(parts) - 1)
            else:
                part += ", us!%d" % (i - 1)
            if i == len(parts) - 1 and circuit["topology"] == "circular":
                part += ", ds!%d" % (len(parts) - 1)
            else:
                part += ", ds!%d" % i
            part += ")"
            init.append(part)
        circuits.append(", ".join(init))

    t = get_template(RBMT["init.ka"])
    docs.insert(0, t.render(circuits = circuits))
    return docs
