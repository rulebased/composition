from operator import attrgetter
from itertools import chain, groupby

from krdf.kasim.ast import AD, RD, VD, OB, IN, TD, AgentD, SiteD

class KappaModel(object):
    def __init__(self, ast):
        """
        :param ast: AST from which to build model
        :type ast: list[kappa_composition.kappa_parser.ast.Statement]
        """
        #: :type: dict[str, kappa_composition.kappa_parser.ast.AgentP]
        self.agents = {}
        #: :type: dict[str, kappa_composition.kappa_parser.ast.VarD]
        self.variables = {}
        #: :type: dict[str, kappa_composition.kappa_parser.ast.Obs]
        self.observations = {}
        #: :type: list[kappa_composition.kappa_parser.ast.Init]
        self.init_values = []
        #: :type: dict[str, kappa_composition.kappa_parser.ast.TokD]
        self.tokens = {}
        #: :type: list[kappa_composition.kappa_parser.ast.Rule]
        self.rules = []
        self._initial_analysis(ast)

        #: :type: list[kappa_composition.kappa_parser.ast.AgentP]
        all_agent_patterns = set(chain.from_iterable(r.lhs[0] + r.rhs[0] for r in self.rules))
        non_declared_agent_patterns = {p for p in all_agent_patterns if p.name not in self.agents}
        key = attrgetter("name")
        grouped_non_declared = {name: list(pats) for name, pats
                                in groupby(sorted(non_declared_agent_patterns, key=key), key=key)}
        for ps in grouped_non_declared.values():
            a = self._derive_agent_declaration_from_patterns(ps)
            self.agents[a.name] = a

    def _initial_analysis(self, ast):
        """
        :type ast: list[kappa_composition.kappa_parser.ast.Statement]
        :return: None
        """
        for statement in ast:
            if isinstance(statement, AD):
                self.agents[statement.agent.name] = statement.agent
            elif isinstance(statement, VD):
                self.variables[statement.var.name] = statement.var
            elif isinstance(statement, OB):
                self.observations[statement.obs.name] = statement.obs
            elif isinstance(statement, TD):
                self.tokens[statement.tok.name] = statement.tok
            elif isinstance(statement, RD):
                self.rules.append(statement.rule)
            elif isinstance(statement, IN):
                self.init_values.append(statement.init)

    @classmethod
    def _derive_agent_declaration_from_patterns(cls, patterns):
        """
        :type patterns: list[kappa_composition.kappa_parser.ast.AgentP]
        :rtype: AgentD
        """
        assert len({p.name for p in patterns}) == 1
        all_sites = []
        all_states = {}
        for p in patterns:
            for s in p.sites:
                all_sites.append(s.site)
                if s.state is not None:
                    all_states.setdefault(s.site, []).append(s.state)
        all_sites = set(all_sites)
        all_states = dict((k, set(v)) for k, v in all_states.items())
        sites = []
        for s in all_sites:
            site = { "site": s }
            if s in all_states:
                site["states"] = all_states[s]
            sites.append(SiteD(site))
        agent = AgentD(patterns[0].name, sites)
        return agent
