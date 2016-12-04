import rdflib

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
    import kappy
    if kappy.namespace_manager is None:
        kappy.namespace_manager = g.namespace_manager
    else:
        g.namespace_manager = kappy.namespace_manager
    return g
