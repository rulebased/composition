from rdflib.parser import Parser, StringInputSource
from rdflib.plugin import register
from rdflib.plugins.parsers.notation3 import TurtleParser

__all__ = 'KrdfParser'

class KrdfParser(Parser):
    __module__ = 'kappy.krdf.KrdfParser'
    def parse(self, source, sink, **args):
        data = source.getByteStream().read()
        turtle = []
        for line in data.split("\n"):
            if line.startswith("#^"):
                turtle.append(line[2:].strip())
        turtle = StringInputSource("\n".join(turtle))
        return TurtleParser().parse(turtle, sink, **args)

register('krdf', Parser, 'kappy.krdf', 'KrdfParser')
register('application/x-kappa', Parser, 'kappy.krdf', 'KrdfParser')
