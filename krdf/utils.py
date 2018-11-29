import rdflib
import logging
from jinja2 import Environment, PackageLoader

def memoize(prop):
    """
    Decorator to remember the result of calling a
    zero-argument method on a class

    >>> class Foo(object):
    ...     n = 0
    ...     @memoize('__getn__')
    ...     def getn(self):
    ...         i = self.n
    ...         self.n += 1
    ...         return i
    >>> foo = Foo()
    >>> foo.getn()
    0
    >>> foo.getn()
    0
    """
    def wrap(f):
        def run(self):
            if not hasattr(self, prop):
                setattr(self, prop, f(self))
            return getattr(self, prop)
        return run
    return wrap


def Graph(*av, **kw):
    """
    We use our own function for creating a graph because
    we want, for aesthetic reasons, to make sure we keep
    all the namespaces that we wish to see.

    >>> g1 = Graph()
    >>> g2 = Graph()
    >>> id(g1.namespace_manager) == id(g2.namespace_manager)
    True
    """
    g = rdflib.Graph(*av, **kw)
    import krdf
    if krdf.namespace_manager is None:
        krdf.namespace_manager = g.namespace_manager
    else:
        g.namespace_manager = krdf.namespace_manager
    return g

def cbd(g, triple, *av, **kw):
    """
    Return the BNode closure(s) for triples that are matched
    by the given "triple". Any additional positional or keyword
    arguments are passed to the constructor for the new graph.
    """
    result = Graph(*av, **kw)
    for s,p,o in g.triples(triple):
        result.add((s,p,o))
        if isinstance(o, rdflib.BNode) and not (o, None, None) in result:
            result += cbd(g, (o, None, None))
    return result

def get_one(g, t):
    triples = list(g.triples(t))
    if len(triples) == 0:
        logging.error("get_one(%s) returned no triples", t)
        return
    if len(triples) > 1:
        logging.error("get_one(%s) returned more than one triple", t)
        return
    return triples[0]

def exists(g, t):
    return len(list(g.triples(t))) == 1

def isstring(s):
    return isinstance(s, str) #or isinstance(s, unicode)

def slug(s):
    sp = s.rsplit("#", 1)
    if len(sp) == 2: return sp[1]
    sp = s.rsplit("/", 1)
    if len(sp) == 2: return sp[1]
    return s

def get_template(name, local_templates=True, **kw):
    if local_templates:
        env = Environment(
            loader=PackageLoader("krdf", "templates"),
            autoescape=False, trim_blocks=True
        )
        _, filename = name.rsplit("/", 1)
        env.globals["curly"] = lambda sym: "{" + sym + "}"
        return env.get_template(filename)
    raise Exception("don't know how to deal with remote templates yet")

def dump_graph(g, format="turtle"):
    for line in g.serialize(format=format).split(b"\n"):
        logging.debug(line)
