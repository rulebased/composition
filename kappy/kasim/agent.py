from kappy.kasim.model import KappaModel
from kappy.kasim import parser

def declare_agents(s):
    ## kludge -- remove coments and escaped newlines
    ss = []
    for l in s.split("\n"):
        l = l.strip()
        if l.startswith("#") or l == "":
            continue
        if l.endswith("\\"):
            l = l[:-1]
        else:
            l = l + "\n"
        ss.append(l)
    s = "".join(ss)
    ast = parser.parseString(s)
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
