from setuptools import setup

setup(
    name="kappy",
    version="0.1",
    packages=["kappy"],
    entry_points = {
        "console_scripts": [
            "kcomp = kappy.kcomp:main"
        ]
    }
)