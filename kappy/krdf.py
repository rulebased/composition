from rdflib.parser import Parser
from rdflib.plugin import register

__all__ = 'KrdfParser'

class KrdfParser(Parser):
    __module__ = 'kappy.KrdfParser'
    def parse(source, sink, **args):
        pass

register('krdf', Parser, 'kappy', 'KrdfParser')

