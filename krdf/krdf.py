import io
from rdflib.parser     import Parser, StringInputSource
from rdflib.serializer import Serializer
from rdflib.plugin     import register
from rdflib.plugins.parsers.notation3 import TurtleParser
from rdflib.plugins.serializers.turtle import TurtleSerializer

__all__ = ['KrdfParser', 'KrdfSerializer']

class KrdfParser(Parser):
    __module__ = 'krdf.krdf.KrdfParser'
    def parse(self, source, sink, **args):
        data = source.getByteStream().read()
        turtle = []
        for line in data.split(b"\n"):
            if line.startswith(b"//^"):
                turtle.append(line[3:].strip())
        turtle = StringInputSource(b"\n".join(turtle))
        return TurtleParser().parse(turtle, sink, **args)

class KrdfSerializer(TurtleSerializer):
    __module__ = 'krdf.krdf.KrdfSerializer'
    def serialize(self, stream, *av, **kw):
        bstream = io.BytesIO()
        super(KrdfSerializer, self).serialize(bstream, *av, **kw)
        bstream.seek(0)
        for line in bstream.readlines():
            stream.write(b"//^ ")
            stream.write(line)

register('krdf', Parser, 'krdf.krdf', 'KrdfParser')
register('application/x-kappa', Parser, 'krdf.krdf', 'KrdfParser')
register('krdf', Serializer, 'krdf.krdf', 'KrdfSerializer')
register('application/x-kappa', Serializer, 'krdf.krdf', 'KrdfSerializer')
