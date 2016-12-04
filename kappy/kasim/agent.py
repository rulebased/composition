from kappy.kasim.model import KappaModel
from kappy.kasim import parser

def declare_agents(s):
    ## kludge
    ss = []
    for l in s.split("\n"):
        l = l.strip()
        if l.startswith("#") or l == "":
            continue
        ss.append(l)
    s = "\n".join(ss)
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

    declarations = """
##
## automatically derived agents
##

""" + "\n".join(agents) + """

##
## end automatically derived agents
##

"""
    return declarations
