import logging
from kasim.agent import declare_agents
from utils import get_template
from namespace import RBMT

def compile_stage4(docs, **kw):
    """
    Derive agent declarations from their usage in the kappa
    documents
    """
    logging.info("stage4: deriving declared agents")
    doc = "\n".join(docs)
    agents = declare_agents(doc)
    agents.sort()
    t = get_template(RBMT["agents.ka"], **kw)
    docs.insert(0, t.render(agents=agents))
    return docs
