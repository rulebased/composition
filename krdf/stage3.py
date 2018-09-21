import logging
from krdf.utils import get_template
from krdf.checks import check_kappa_rules, check_rdf_syntax

def compile_stage3(ir, debug=False, **kw):
    """
    For each circuit, for each part, make the appropriate substitutions in
    the templates
    """
    logging.info("stage3: performing substitutions on templates")
    symbols = {
        "type": type,
        "len": len
    }
    docs = []
    for circuit in ir["circuits"]:
        for part in circuit["parts"]:
            logging.info("stage3: %s" % (part["uri"],))
            template = get_template(part["template"])
            part.update(symbols)
            doc = template.render(model=ir, circuit=circuit, **part)
            docs.append(doc)

    for protein in ir["proteins"]:
        print(protein)
        template = get_template(protein["template"])
        doc = template.render(model=ir, **protein)
        docs.append(doc)

    logging.debug("="*80)
    logging.debug("stage3: output")
    for doc in docs:
        logging.debug("-"*80)
        for line in doc.split("\n"):
            logging.debug(line)
        logging.debug("."*80)
        check_rdf_syntax(doc)
        check_kappa_rules(doc)
    logging.debug("="*80)

    return docs
