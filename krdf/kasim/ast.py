from abc import ABCMeta
from krdf.utils import isstring

def _assert_all_is_instance(iterable, klass):
    for o in iterable:
        assert isinstance(o, klass), repr(o)

def _assert_all_isstring(iterable):
    "ugh"
    for o in iterable:
        assert isstring(o), o

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
        return hash(tuple(self.__dict__.items()))

    def __str__(self):
        items = self.__dict__.items()
        attrs = ' '.join('%s=%s' % (attr, val) for attr, val in items)
        type_name = type(self).__name__
        return '<%s %s>' % (type_name, attrs) if attrs else "<%s>" % type_name

    def __repr__(self):
        return str(self)


class LinkP(ASTBase):
    pass


class BoundLink(LinkP):
    def __str__(self):
        return "[_]"

class UnboundLink(LinkP):
    def __str__(self):
        return "[.]"

class MaybeBoundLink(LinkP):
    def __str__(self):
        return "[#]"

class Link(LinkP):
    def __init__(self, text):
        """
        :param text: annotation for a link
        :type text: str
        """
        assert isstring(text), text
        self.text = text
    def __str__(self):
        return "[" + self.text + "]"

class BondStub(LinkP):
    def __init__(self, stub):
        self.stub = stub
    def __str__(self):
        return "[" + ".".join(self.stub) + "]"

class SiteP(ASTBase):
    def __init__(self, parsed):
        self.site = parsed["site"]
        self.link = parsed["link"]
        self.state = parsed["state"][0] if "state" in parsed else None

    def __str__(self):
        s = self.site
        if self.state is not None:
            s += "{" + str(self.state) + "}"
        s += str(self.link)
        return s
    def __hash__(self):
        return hash(self.site)

class AgentP(ASTBase):
    def __init__(self, parsed):
        self.name = parsed["name"]
        self.sites = parsed["sites"] if "sites" in parsed else ""

    def __hash__(self):
        return hash((self.name, tuple(self.sites)))

    def __str__(self):
        return self.name + "(" + ", ".join(str(s) for s in self.sites) + ")"

class AgentN(ASTBase):
    def __init__(self, parsed):
        pass
    def __str__(self):
        return "."

class SiteD(ASTBase):
    """
    Site definition
    """
    def __init__(self, parsed):
        self.name = parsed["site"]
        self.bindings = parsed.get("bindings", [])
        self.states = parsed.get("states", [])
    def __str__(self):
        s = self.name
        if len(self.bindings) > 0:
            s += "[" + " ".join(".".join(b) for b in self.bindings) + "]"
        if len(self.states) > 0:
            s += "{" + " ".join("%s" % s for s in self.states) + "}"
        return s

class AgentD(ASTBase):
    """
    Agent definition
    """
    def __init__(self, name, sites):
        """
        :param name: human-readable name of an agent
        :type name: str

        :param sites: mapping between site names of an agent and their possible values
        :type sites: dict[str, frozenset[str]]
        """
        assert isstring(name), name
        self.name = name
        self.sites = sites

    def __str__(self):
        return self.name + "(" + ", ".join(str(s) for s in self.sites) + ")"
    def __hash__(self):
        return hash((self.name, tuple(self.sites.items())))


class Expr(ASTBase):
    __metaclass__ = ABCMeta


class Var(Expr):
    def __init__(self, name):
        """
        :param name: variable's name
        :type name: str
        """
        assert isstring(name), name
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
        :type name: str

        :param expr: token's expressions
        :type expr: Expr
        """
        assert isinstance(name, str), name
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
        :type lhs: tuple[tuple[AgentP], tuple[TokE]]

        :param rhs: result part of a rule
        :type rhs: tuple[tuple[AgentP], tuple[TokE]]

        :param rate: rate of a rule
        :type rate: Expr

        :param rate_c: ???
        :type rate_c: Expr

        :param desc: rule human-readable description
        :type desc: str
        """
        # TODO: type validation for lhs and rhs
        assert isinstance(rate, Expr), rate
        assert isinstance(rate_c, Expr), rate_c
        assert isstring(desc), desc
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
        :type name: str

        :param expr: expression to bind to variable
        :type expr: Expr
        """
        assert isinstance(name, str), name
        assert isinstance(expr, Expr), name
        self.name = name
        self.expr = expr


# data TokD = TokD Text deriving (Show, Eq, Ord)
class TokD(ASTBase):
    def __init__(self, name):
        """
        :param name: token's name
        :type name: str
        """
        assert isinstance(name, str), str
        self.name = name


# data Obs  = Obs Text AgentP deriving (Show, Eq, Ord)
class Obs(ASTBase):
    def __init__(self, name, pattern):
        """
        :param name: name of an observation
        :type name: str

        :param pattern: pattern to observe
        :type pattern: AgentP
        """
        assert isinstance(name, str), name
        assert isinstance(pattern, AgentP), pattern
        self.name = name
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
        :type value: str
        """
        assert isstring(value), value
        self.value = value
