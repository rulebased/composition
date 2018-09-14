from krdf.kasim import ast, parser

def test_binding_sig():
    b = parser.binding_sig.parseString("[a.B c.D]")
    assert list(b["bindings"]) == [("a", "B"), ("c", "D")], b

def test_agent():
    agent_sigs = [
        "A(x, c)",
        "B(x)",
        "D(y[x.A])",
        "E(y[x.A y.B])",
        "C(x1{u p}, x2{u p})",
        "A(x[a.B y.A]{u p}, y[x.A], z{z1 z2 z3})"
    ]
    for sig in agent_sigs:
        a = parser.agent_sig.parseString(sig)
        assert len(a) == 1, sig
        assert str(a[0]) == sig, sig

def test_link_pat():
    links = [
        ("[1]", ast.Link),
        ("[_]", ast.BoundLink),
        ("[.]", ast.UnboundLink),
        ("[x.A]", ast.BondStub),
        ("[#]", ast.MaybeBoundLink),
        ("", ast.MaybeBoundLink)
    ]
    for s, cls in links:
        l = parser.link_pat.parseString(s)
        assert len(l) == 1, s
        assert isinstance(l[0], cls), s

def test_site_pat():
    pats = [
        "x",
        "x{abc}",
        "x[1]",
        "x{abc}[1]",
        "x{#}"
    ]
    for pat in pats:
        p = parser.site_pat.parseString(pat)
        assert len(p) == 1, p

def test_agent_pat():
    agent_pats = [
        "A()",
        "A(x[.])",
        "A(x[_])",
        "A(x[#])",
        "A(x[1])",
        "A(x[y.B])",
        "A(x[1], y[y.A])",
        "A(x{foo}[#], z[1])"
    ]
    for pat in agent_pats:
        a = parser.agent_pat.parseString(pat)
        assert len(a) == 1, pat
        assert str(a[0]) == pat, pat

    abbrv_pats = [
        ("A(x)", "A(x[#])"),
        ("A(x{foo})", "A(x{foo}[#])")
    ]
    for abbrv, pat in abbrv_pats:
        a = parser.agent_pat.parseString(abbrv)
        assert len(a) == 1, pat
        assert str(a[0]) == pat, pat
