from setuptools import setup

setup(
    name="kappy",
    version="0.1",
    packages=["kappy"],
    setup_requires=['nose'],
    entry_points = {
        "console_scripts": [
            "kcomp = kappy.kcomp:main",
            "kdumpviz = kappy.kviz:main"
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
