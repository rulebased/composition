from FuXi.Rete.RuleStore import SetupRuleStore
from FuXi.Rete.Util import generateTokenSet
from FuXi.Horn.HornRules import HornFromN3
import logging
from krdf.utils import Graph

def compile_stage1(model, facts = [], rules = [], **kw):
    logging.info("stage1: setting up inference rules")
    _, _, network = SetupRuleStore(makeNetwork = True)
    for ruleset in rules:
        logging.info("stage1: loading rules %s" % ruleset)
        for rule in HornFromN3(ruleset):
            network.buildNetworkFromClause(rule)

    data = Graph()
    for factset in facts:
        logging.info("stage1: loading facts %s" % factset)
        data += Graph().parse(factset, format="turtle")


    logging.info("stage1: loading model %s" % model)
    data += Graph().parse(model, format="turtle")

    logging.info("stage1: generating inferred intermediate representation")
    network.inferredFacts = data
    network.feedFactsToAdd(generateTokenSet(data))


    logging.debug("=")
    logging.debug("stage1: output")
    logging.debug("-"*80)
    for line in data.serialize(format="turtle").split(b"\n"):
        logging.debug(line)
    logging.debug("="*80)

    return data
