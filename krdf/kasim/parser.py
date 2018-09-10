from __future__ import absolute_import, print_function

from pyparsing import *

from . import ast

ParserElement.enablePackrat()

# Utility parser -- consume 0 or more whitespaces
many_space = Optional(White()).suppress()
#many_space = many_space_ + Optional(Literal("\\") + lineEnd + many_space_).suppress()

# Utility parser -- parse a floating point number
double = Combine(Optional(Literal("-")) + Word(nums) + Optional(Literal(".") + Word(nums)))\
    .setParseAction(lambda toks: float(toks[0]))

# Utility parser -- parse a token/name
tok = Combine(Word(alphas, exact=1) + Optional(Word(alphanums + "_+-")))

# Utility parser -- parse a single-quoted token/name
qtok = Suppress("'") + tok + Suppress("'")

# Utility parser -- parse a state token
stok = Word(alphanums + "_+-")

# Utility parser -- parse a single-quoted string
qstr = Suppress("'") + CharsNotIn("'") + Suppress("'")

# Utility parser -- eat a comment until end of line
comment = Suppress("//") + (lineEnd ^ (CharsNotIn("^\r\n", exact=1) + SkipTo(lineEnd))).suppress()

# Utility parser -- eat up until end of line
eol = (many_space + comment) ^ lineEnd.suppress()

bare_site_sig = tok.setParseAction(lambda toks: toks[0]).setResultsName("site")
binding_site_sig = And([tok, Suppress("."), tok]).setParseAction(lambda toks: tuple(toks))
binding_sig = And([Suppress("["), ZeroOrMore(binding_site_sig), Suppress("]")]).setResultsName("bindings")
internal_state_sig = And([Suppress("{"), ZeroOrMore(tok), Suppress("}")]).setResultsName("states")
site_sig = And([bare_site_sig, Optional(binding_sig), Optional(internal_state_sig)])\
           .setParseAction(ast.SiteD)

# AgentD
agent_sig = And([tok, Suppress("("), Group(delimitedList(site_sig, delim=",")), Suppress(")")])\
    .setParseAction(lambda toks: ast.AgentD(toks[0], list(toks[1])))

# Statement
agent_dec = (Suppress("%agent:") + many_space + agent_sig).setParseAction(lambda toks: ast.AD(toks[0]))

# Statement
tok_dec = Suppress("%token:") + many_space + qtok.copy().setParseAction(lambda toks: ast.TD(ast.TokD(toks[0])))

expr = Forward()

# Statement
var_dec = (Literal("%var:").suppress() + many_space + qtok + many_space + expr) \
    .setParseAction(lambda toks: ast.VD(ast.VarD(toks[0], toks[1])))


e_var = qtok.copy().setParseAction(lambda toks: ast.Var(toks[0]))

e_lit = double.copy().addParseAction(lambda toks: ast.Lit(toks[0]))

e_bracket = Suppress("(") + many_space + expr + many_space + Suppress(")")

e_neg = (Suppress("-") + expr).setParseAction(lambda toks: ast.Neg(toks[0]))


def e_op(op, op_token):
    """
    :param op: AST operator, must be subclass of ast.UnaryCompositeExpr
    :type op: type

    :param op_token: text representation of this operand
    :type op_token: str

    :return: parser for this operator
    :rtype: ParserElement
    """
    assert issubclass(op, ast.UnaryCompositeExpr)
    return (Suppress(op_token) + expr).setParseAction(lambda toks: op(toks[0]))


def e_binop(op, op_token):
    """
    :param op: AST operator, must be subclass of ast.UnaryCompositeExpr
    :type op: type

    :param op_token: text representation of this operand
    :type op_token: str

    :return: parser for this operator
    :rtype: ParserElement
    """
    assert issubclass(op, ast.BinaryCompositeExpr)
    return And([Suppress(op_token), Suppress("("), many_space, expr, many_space, Suppress(","),
                many_space, expr, many_space, Suppress(")")]).setParseAction(lambda toks: op(toks[0], toks[1]))

infix_term = Or([
    e_bracket,
    e_var,
    e_lit,
    e_neg,
    e_op(ast.Log, "[log]"),
    e_op(ast.Abs, "[abs]"),
    e_op(ast.Floor, "[int]"),
    e_op(ast.Exp, "[exp]"),
    e_op(ast.Cos, "[cos]"),
    e_op(ast.Sin, "[sin]"),
    e_op(ast.Tan, "[tan]"),
    e_binop(ast.Max, "[max]"),
    e_binop(ast.Min, "[min]")
])

infix_nodes = {
    "+": ast.Plus,
    "-": ast.Minus,
    "*": ast.Times,
    "/": ast.Div,
    "[mod": ast.Mod,
    "^": ast.Pow
}


# pyparsing infixNotation helper has a strange behavior of grouping successive operands for a same operator into a
# single group. For example parsing "1+2+3" will yield [1, '+', 2, '+', 3] instead of [[1, '+', 2], '+', 3]. This ugly
# action reverses this kind of grouping. That ONLY happens for opAssoc.LEFT operations, so no need to handle pow case
# See http://pyparsing.wikispaces.com/share/view/73472016
def _infix_action(toks):
    toks = toks[0]
    assert len(toks) >= 3, toks
    assert len(toks) % 2 == 1, "Expecting odd number of tokens"
    op = toks[1]
    result = infix_nodes[op](toks[0], toks[2])
    remaining = toks[3:]
    if not remaining:
        return result
    else:
        return _infix_action([[result] + remaining])


expr <<= infixNotation(infix_term, [
    (oneOf('^'), 2, opAssoc.RIGHT, _infix_action),
    (oneOf('* / [mod]'), 2, opAssoc.LEFT, _infix_action),
    (oneOf('+ -'), 2, opAssoc.LEFT, _infix_action)
])


link_pat_linked = Suppress("[") + stok.copy().setParseAction(lambda toks: ast.Link(toks[0])) + Suppress("]")
link_pat_bound = Suppress("[_]").setParseAction(lambda _: ast.BoundLink())
link_pat_unbound = Suppress("[.]").setParseAction(lambda _: ast.UnboundLink())
link_pat_stub = Suppress("[") + binding_site_sig.copy().setParseAction(lambda stub: ast.BondStub(stub)) + Suppress("]")
link_pat_explicit_mbound = Suppress("[#]").setParseAction(lambda _: ast.MaybeBoundLink())
link_pat_mbound = Empty().setParseAction(lambda _: ast.MaybeBoundLink())
link_pat = Or([
    link_pat_bound,
    link_pat_linked,
    link_pat_unbound,
    link_pat_stub,
    link_pat_mbound,
    link_pat_explicit_mbound
]).setResultsName("link").setName("link pattern")

site_state_pat = And([Suppress("{"), tok, Suppress("}")]).setResultsName("state")
site_pat = And([
    tok.copy().setResultsName("site"),
    Optional(site_state_pat),
    link_pat
]).setParseAction(ast.SiteP).setName("site pattern")

agent_pat = And([
    tok.copy().setResultsName("name"),
    Suppress("("),
    Optional(delimitedList(site_pat, delim=","))("sites"),
    Suppress(")")
]).setParseAction(ast.AgentP).setName("agent pattern")

tok_expr = (expr + many_space + Suppress(":") + many_space + qtok).setParseAction(lambda ts: ast.TokE(ts[1], ts[0]))

tok_exprs = many_space + Suppress("|") + many_space + delimitedList(tok_expr)

pure_rule = And([
    qtok("desc"),
    many_space,
    Group(delimitedList(Optional(agent_pat)))("lhs_agents"),
    Optional(tok_expr)("lhs_tokens"),
    many_space, Suppress("->"), many_space,
    Group(delimitedList(Optional(agent_pat)))("rhs_agents"),
    Optional(tok_expr)("rhs_tokens"),
    many_space, Suppress("@"), many_space,
    expr("rate")
]).setParseAction(lambda ts: [ast.Rule(lhs=(tuple(ts.lhs_agents), tuple(ts.lhs_tokens)),
                                       rhs=(tuple(ts.rhs_agents), tuple(ts.rhs_tokens)),
                                       rate=ts.rate, desc=ts.desc[0])])

bi_rule = And([
    qtok("desc"),
    many_space,
    Group(delimitedList(Optional(agent_pat)))("lhs_agents"),
    Optional(tok_expr)("lhs_tokens"),
    many_space, Suppress("<->"), many_space,
    Group(delimitedList(Optional(agent_pat)))("rhs_agents"),
    Optional(tok_expr)("rhs_tokens"),
    many_space, Suppress("@"), many_space,
    expr("rate_forward"),
    many_space, Suppress(","), many_space,
    expr("rate_backward"),
]).setParseAction(lambda ts: [ast.Rule(lhs=(tuple(ts.lhs_agents), tuple(ts.lhs_tokens)),
                                       rhs=(tuple(ts.rhs_agents), tuple(ts.rhs_tokens)),
                                       rate=ts.rate_forward, desc=ts.desc),
                              ast.Rule(lhs=(tuple(ts.rhs_agents), tuple(ts.rhs_tokens)),
                                       rhs=(tuple(ts.lhs_agents), tuple(ts.lhs_tokens)),
                                       rate=ts.rate_backward, desc=ts.desc[0])])

circ_rule = And([
    qtok("desc"),
    many_space,
    Group(delimitedList(Optional(agent_pat)))("lhs_agents"),
    Optional(tok_expr)("lhs_tokens"),
    many_space, Suppress("->"), many_space,
    Group(delimitedList(Optional(agent_pat)))("rhs_agents"),
    Optional(tok_expr)("rhs_tokens"),
    many_space, Suppress("@"), many_space,
    expr("rate"),
    many_space, Suppress("("), many_space,
    expr("rate_c"),
    many_space, Suppress(")")
]).setParseAction(lambda ts: [ast.Rule(lhs=(tuple(ts.lhs_agents), tuple(ts.lhs_tokens)),
                                       rhs=(tuple(ts.rhs_agents), tuple(ts.rhs_tokens)),
                                       rate=ts.rate, rate_c=ts.rate_c, desc=ts.desc[0])])

rule_pat = pure_rule ^ bi_rule ^ circ_rule

rule_dec = rule_pat.copy().setParseAction(lambda ts: ast.RD(ts[0]))

obs_dec = (Suppress("%obs:") + many_space + qtok + many_space + agent_pat).\
    setParseAction(lambda ts: ast.OB(ast.Obs(ts[0], ts[1])))

init_dec = (Suppress("%init:") + many_space + double + many_space + Group(delimitedList(agent_pat))).\
    setParseAction(lambda ts: ast.IN(ast.Init(ts[0], ts[1])))

rdf_line = (Suppress("//^ ") + CharsNotIn("\n") + lineEnd.suppress()).setParseAction(lambda ts: ast.RDF(ts[0]))

statement = rdf_line ^ agent_dec ^ var_dec ^ tok_dec ^ rule_dec ^ obs_dec ^ init_dec

kappa_parser = ZeroOrMore(eol) + ZeroOrMore(statement + ZeroOrMore(eol))

def parseString(s):
    ## kludge -- remove coments and escaped newlines
    ## parser above doesn't deal properly with them
#    if isinstance(s, str):
#        s = unicode(s)
    ss = []
    for l in s.split(u"\n"):
        l = l.strip()
        if l.startswith(u"//") or l == "":
            continue
        if l.endswith(u"\\"):
            l = l[:-1]
        else:
            l = l + u"\n"
        ss.append(l)
    s = u"".join(ss)

    parsed = kappa_parser.parseString(s)

    nrules = len(list(r for r in s.split(u"\n") if len(r) > 0))
    if nrules != len(parsed):
        print(s)
        for p in parsed:
            print(p)
        raise Exception("Substituted template parse error")

    return parsed
