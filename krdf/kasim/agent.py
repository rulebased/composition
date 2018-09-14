from krdf.kasim.model import KappaModel
from krdf.kasim import parseString

def declare_agents(s):
    ast = parseString(s)
    kasim = KappaModel(ast)

    agents = []
    for a in kasim.agents.values():
        agents.append("%%agent: %s" % a)
    return agents
