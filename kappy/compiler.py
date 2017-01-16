from stage1 import compile_stage1
from stage2 import compile_stage2
from stage3 import compile_stage3
from stage4 import compile_stage4
from stage5 import compile_stage5
from stage6 import compile_stage6

from merge import merge

def compile(model, **kw):
    ## ir1 is materialised rdf graph
    ir1 = compile_stage1(model, **kw)
    ## ir2 is dictionary
    ir2 = compile_stage2(ir1, **kw)
    ## ir3 is a list of kappa documents
    ir3 = compile_stage3(ir2, **kw)
    ## ir4 adds derived agent declarations
    ir4 = compile_stage4(ir3, **kw)
    ## ir5 adds the host environment
    ir5 = compile_stage5(ir1, ir4, **kw)
    ## ir5 adds initialisation for the circuits
    ir6 = compile_stage6(ir2, ir5, **kw)
    ## produce final output
    merged = merge(model, ir6)
    return merged
