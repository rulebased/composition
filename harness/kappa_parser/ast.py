from __future__ import unicode_literals

from functools import total_ordering
from abc import ABCMeta


def _assert_all_is_instance(iterable, klass):
    for o in iterable:
        assert isinstance(o, klass), o


class ASTBase(object):
    """
    Just providing a value semantics to all inheriting AST elements
    """
    __metaclass__ = ABCMeta

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__dict__.items())

    def __lt__(self, other):
        assert type(self) == type(other)  # generally we don't want allow cross-classes comparisons
        return self.__dict__.items() < other.__dict__.items()

    def __unicode__(self):
        items = self.__dict__.items()
        attrs = ' '.join('%s=%s' % (attr, val) for attr, val in items)
        type_name = type(self).__name__
        return '<%s %s>' % (type_name, attrs) if attrs else "<%s>" % type_name

    def __str__(self):
        return unicode(self).encode()

    def __repr__(self):
        return str(self)


# data LinkP   = Bound | Unbound | MaybeBound | Link Text deriving (Eq, Ord)
class LinkP(ASTBase):
    # TODO: implement proper ordering
    pass


class BoundLink(LinkP):
    pass
BoundLink = BoundLink()  # Fancy way to make it something like singleton. Lets see how will it work.


class UnboundLink(LinkP):
    pass
UnboundLink = UnboundLink()


class MaybeBoundLink(LinkP):
    pass
MaybeBoundLink = MaybeBoundLink()


class Link(LinkP):
    def __init__(self, text):
        """
        :param text: annotation for a link
        :type text: unicode
        """
        assert isinstance(text, unicode)
        self.text = text


# data StateP  = State Text | Undefined deriving (Eq, Ord)

class StateP(ASTBase):
    # TODO: implement proper ordering
    pass


class State(StateP):
    def __init__(self, text):
        """
        :param text: annoutation for a state
        :type text: unicode
        """
        assert isinstance(text, unicode), text
        self.text = text


class UndefinedState(StateP):
    pass
UndefinedState = UndefinedState()


# type SiteP   = (LinkP, StateP)
@total_ordering
class SiteP(ASTBase):
    def __init__(self, link, state):
        """
        :param link: link state of a site
        :type link: LinkP

        :param state: internal state of a site
        :type state: StateP
        """
        assert isinstance(link, LinkP), link
        assert isinstance(state, StateP), state
        self.link = link
        self.state = state


# data AgentP  = AgentP Text (HashMap Text SiteP) deriving(Eq)
@total_ordering
class AgentP(ASTBase):
    def __init__(self, name, sites):
        """
        :param name: agent's human-readable name
        :type name: unicode

        :param sites: mapping between site names and sites
        :type sites: dict[unicode, SiteP]
        """
        assert isinstance(name, unicode), name
        assert isinstance(sites, dict)
        _assert_all_is_instance(sites.keys(), unicode)
        _assert_all_is_instance(sites.values(), SiteP)
        self.name = name
        self.sites = sites

    def __lt__(self, other):
        """
        :type other: AgentP
        :rtype: bool
        """
        return (self.name, self.sites.items()) < (other.name, other.sites.items())


# data AgentD = AgentD Text (HashMap Text [Text]) deriving(Eq)
@total_ordering
class AgentD(ASTBase):
    """
    Agent definition
    """
    def __init__(self, name, sites):
        """
        :param name: human-readable name of an agent
        :type name: unicode
        :param sites: mapping between site names of an agent and their possible values
        :type sites: dict[unicode, tuple[unicode]]
        """
        assert isinstance(name, unicode), name
        _assert_all_is_instance(sites.keys(), unicode)
        for site in sites.values():
            assert isinstance(site, tuple), tuple
            _assert_all_is_instance(site, unicode)
        self.name = name
        self.sites = sites

    def __lt__(self, other):
        """
        :type other: AgentD
        :rtype: bool
        """
        return (self.name, sorted(self.sites.items())) < (other.name, sorted(other.sites.items()))


class Expr(ASTBase):
    __metaclass__ = ABCMeta


class Var(Expr):
    def __init__(self, name):
        """
        :param name: variable's name
        :type name: unicode
        """
        assert isinstance(name, unicode), name
        self.name = name


class Lit(Expr):
    def __init__(self, value):
        """
        :param value: numeric literal's value
        :type value: float
        """
        assert isinstance(value, float), value
        self.value = value


class UnaryCompositeExpr(Expr):
    def __init__(self, expr):
        """
        :param expr: expression to wrap
        :type expr: Expr
        """
        assert isinstance(expr, Expr), expr
        self.expr = expr


class Neg(UnaryCompositeExpr):
    pass


class Abs(UnaryCompositeExpr):
    pass


class Floor(UnaryCompositeExpr):
    pass


class Exp(UnaryCompositeExpr):
    pass


class Cos(UnaryCompositeExpr):
    pass


class Sin(UnaryCompositeExpr):
    pass


class Tan(UnaryCompositeExpr):
    pass


class Log(UnaryCompositeExpr):
    pass


class BinaryCompositeExpr(Expr):
    def __init__(self, lhs, rhs):
        """
        :param lhs: left operand
        :type lhs: Expr

        :param rhs: right operana
        :type rhs: Expr
        """
        assert isinstance(lhs, Expr), lhs
        assert isinstance(rhs, Expr), rhs
        self.lhs = lhs
        self.rhs = rhs


class Min(BinaryCompositeExpr):
    pass


class Max(BinaryCompositeExpr):
    pass


class Plus(BinaryCompositeExpr):
    pass


class Minus(BinaryCompositeExpr):
    pass


class Times(BinaryCompositeExpr):
    pass


class Pow(BinaryCompositeExpr):
    pass


class Div(BinaryCompositeExpr):
    pass


class Mod(BinaryCompositeExpr):
    pass


# data TokE    = Tok Text Expr deriving(Show, Eq, Ord)
class TokE(ASTBase):
    def __init__(self, name, expr):
        """
        :param name: token's name
        :type name: unicode

        :param expr: token's expressions
        :type expr: Expr
        """
        assert isinstance(name, unicode), name
        assert isinstance(expr, Expr), expr
        self.name = name
        self.expr = expr


# data Rule = Rule { lhs:: ([AgentP], [TokE])
#                  , rhs:: ([AgentP], [TokE])
#                  , rate:: Expr
#                  , rateC:: Expr
#                  , desc:: Text
#                  }
# deriving(Show, Eq)
class Rule(ASTBase):
    def __init__(self, lhs, rhs, rate, rate_c=Lit(0.0), desc=""):
        """
        :param lhs: origin part of a rule
        :type lhs: tuple[tuple[AgentP], tuple[TokE]] | None

        :param rhs: result part of a rule
        :type rhs: tuple[tuple[AgentP], tuple[TokE]] | None

        :param rate: rate of a rule
        :type rate: Expr

        :param rate_c: ???
        :type rate_c: Expr

        :param desc: rule human-readable description
        :type desc: unicode
        """
        # TODO: type validation for lhs and rhs
        assert isinstance(rate, Expr), rate
        assert isinstance(rate_c, Expr), rate_c
        assert isinstance(desc, unicode), desc
        self.lhs = lhs
        self.rhs = rhs
        self.rate = rate
        self.rate_c = rate_c
        self.desc = desc


# data VarD = VarD Text Expr deriving (Show, Eq, Ord)
class VarD(ASTBase):
    def __init__(self, name, expr):
        """
        :param name: name of a variable
        :type name: unicode

        :param expr: expression to bind to variable
        :type expr: Expr
        """
        assert isinstance(name, unicode), name
        assert isinstance(expr, Expr), name
        self.name = name
        self.expr = expr


# data TokD = TokD Text deriving (Show, Eq, Ord)
class TokD(ASTBase):
    def __init__(self, name):
        """
        :param name: token's name
        :type name: unicode
        """
        assert isinstance(name, unicode), unicode
        self.name = name


# data Obs  = Obs Text AgentP deriving (Show, Eq, Ord)
class Obs(ASTBase):
    def __init__(self, name, pattern):
        """
        :param name: name of an observation
        :type name: unicode

        :param pattern: pattern to observe
        :type pattern: AgentP
        """
        assert isinstance(name, unicode), name
        assert isinstance(pattern, AgentP), pattern
        self.pattern = pattern


# data Init = Init Double [AgentP] deriving (Show, Eq, Ord)
class Init(ASTBase):
    def __init__(self, value, patterns):
        """
        :param value: initial value
        :type value: float

        :param patterns: agent patterns
        :type patterns: tuple[AgentP]
        """
        assert isinstance(value, float), value
        for p in patterns:
            assert isinstance(p, AgentP), p
        self.value = value
        self.patterns = patterns


# data Statement = AD AgentD | VD VarD | TD TokD | RD Rule | OB Obs | IN Init | RDF Text
class Statement(ASTBase):
    __metaclass__ = ABCMeta


class AD(Statement):
    """
    Agent declaration
    """
    def __init__(self, agent):
        """
        :param agent: declared agent
        :type agent: AgentD
        """
        assert isinstance(agent, AgentD), agent
        self.agent = agent


class VD(Statement):
    """
    Variable declaration
    """
    def __init__(self, var):
        """
        :param var: declared variable
        :type var: VarD
        """
        assert isinstance(var, VarD), var
        self.var = var


class TD(Statement):
    """
    Token declaration
    """
    def __init__(self, tok):
        """
        :param tok: declared token
        :type tok: TokD
        """
        assert isinstance(tok, TokD), tok
        self.tok = tok


class RD(Statement):
    """
    Rule declaration
    """
    def __init__(self, rule):
        """
        :param rule: declared rule
        :type rule: Rule
        """
        assert isinstance(rule, Rule), rule
        self.rule = rule


class OB(Statement):
    """
    Observation declaration
    """
    def __init__(self, obs):
        """
        :param obs: declared observation
        :type obs: Obs
        """
        assert isinstance(obs, Obs), obs
        self.obs = obs


class IN(Statement):
    """
    Init value declaration
    """
    def __init__(self, init):
        """
        :param init: declared init value
        :type init: Init
        """
        assert isinstance(init, Init), init
        self.init = init


class RDF(Statement):
    """
    RDF annotation
    """
    def __init__(self, value):
        """
        :param value: annotation text
        :type value: unicode
        """
        assert isinstance(value, unicode), value
        self.value = value
