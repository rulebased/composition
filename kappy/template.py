from kappy.hybrid import KappaRdf
from kappy.utils import memoize

class TemplateError(Exception):
    "Raised when there is a problem with a template"

class Template(KappaRdf):
    def data(self):
        prefix = None
        for pfx, ns in self.namespace_manager.namespaces():
            if pfx == "model":
                prefix = "@prefix : <%s>." % ns
                break
        if prefix is None:
            for pfx, ns in self.namespace_manager.namespaces():
                print pfx, ns
            raise TemplateError("We do not have the empty prefix available :(")

        raw = KappaRdf.data(self)
        if "#^" in raw:
            prefix = "#^ " + prefix

        data = prefix + "\n" + raw

        return data
