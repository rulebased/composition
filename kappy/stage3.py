import logging
from utils import get_template

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
            template = get_template(part["template"])
            part.update(symbols)
            docs.append(template.render(model=ir, circuit=circuit, **part))

    logging.debug("="*80)
    logging.debug("stage3: output")
    for doc in docs:
        logging.debug("-"*80)
        for line in doc.split("\n"):
            logging.debug(line)
    logging.debug("="*80)

    return docs
