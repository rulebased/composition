from krdf.kasim.model import KappaModel
from krdf.kasim import parseString

def declare_agents(s):
    ast = parseString(s)
    kasim = KappaModel(ast)

    agents = []
    for a in kasim.agents.values():
        agent = "%%agent: %s(" % a.name
        sitenames = a.sites.keys()
        sitenames.sort()
        sites = []
        for name in sitenames:
            site = name
            if len(a.sites[name]) > 0:
                site = site + "~" + "~".join(a.sites[name])
            sites.append(site)
        agent = agent + ",".join(sites) + ")"
        agents.append(agent)

    return agents
