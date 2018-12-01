# Composition of Genetic Parts for Synthetic Biology

This software repository contains a Python library and example programs
for composing and simulating synthetic genetic circuits. The simulation
routines require the [KaSim](https://kappalanguage.org/) program to be
installed and on the search path.

Installation is recommended under [miniconda](https://conda.io/miniconda.html)
but may be installed and run under any Python3 version. Installation is
as follows:

    % pip install -r pip-requirements.txt
    % python setup.py install

This will result in several command-line programs being made available:

 * `kcomp` - the [Genetic Circuit Compiler](https://pubs.acs.org/doi/abs/10.1021/acssynbio.8b00201).
    It takes a description of a genetic circuit in the Turtle language
    and produces a simulation program for KaSim.
 * `krun` - Runs a simulation of a genetic circuit on the simulator back-end.
    It takes a partly specified circuit and an optional auxilliary Turtle 
    file (usefully, a parts database with protein descriptions and so forth).
 * `kgen` - Executes an evolutionary algorithm to discover oscillatory circuits.
 * `ksim` - Worker back-end program that executes simulations.
 * `kq` - Dispatcher program that parcels out request from `krun` or `kgen` to
   `ksim` workers.

The last four programs are typically used together. One `kq` instance is
required and potentially many `ksim` workers running with as many threads
as there are processors on the system. Setup for computation on a single
host with 12 CPU cores means running,

    % kq &
    % ksim -t 12

It is possible to run `ksim` instances on many hosts and request using the
`-s` option that they all connect to the same `kq` instance.

Then a circuit may be requested to run on the back-end:

    % krun -l 1000000 examples/repressilator.ttl

where the `-l` argument indicates the number of time-steps to run for.

To discover a two-operon oscillator and place the results in a directory 
called data, one can run:

    % mkdir data
    % kgen -l 100000 examples/twoop.ttl partsdb.ttl data
    0.542677        OLacIa PrRMb B0034c CTetRd B0011e OTetRf PrRMg B0034h CLacIi B0011j
    0.361204        OLcIa PrRMb B0034c CTetRd B0011e OTetRf PrRMg B0034h CLcIi B0011j
    0.286513        OLacIa PrRFb B0034c CTetRd B0011e OTetRf PrRMg B0034h CLcIi B0011j
    0.188044        OTetRa PrISb B0034c CTetRd B0011e OLcIf PrRMg B0034h CLcIi B0011j

and one sees that the two best results are indeed  the kind of oscillators
that were required.
