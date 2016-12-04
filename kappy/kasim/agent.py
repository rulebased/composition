from kappy.kasim.model import KappaModel
from kappy.kasim import parser

def declare_agents(s):
    ast = parser.parseString(s)
    kasim = KappaModel(ast)
    print kasim.agents
    print ast
    raise "adasd"
