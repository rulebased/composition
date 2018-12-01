from setuptools import setup

setup(
    name="krdf",
    version="0.1",
    packages=["krdf"],
    setup_requires=['nose'],
    entry_points = {
        "console_scripts": [
            "kcomp = krdf.kcomp:main",
            "kdumpviz = krdf.kviz:main",
            "kgen = krdf.kgen:main",
            "ksim = krdf.ksim:main",
            "kq = krdf.kq:main",
            "krun = krdf.krun:main"
        ]
    },
    data_files = [
        ("rdf", ["rdf/rdfs-rules.n3",
                 "rdf/owl-rules.n3",
                 "rdf/composition.n3",
                 "rdf/composition.ttl"]
        ),
        ("templates", ["templates/operator.ka",
                       "templates/promoter.ka"]
        )
    ]
)
