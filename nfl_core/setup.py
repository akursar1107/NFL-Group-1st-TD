from setuptools import setup

setup(
    name="nfl-core",
    version="1.0.0",
    description="Shared NFL statistics and data utilities",
    author="Your Name",
    py_modules=["nfl_core.config", "nfl_core.data", "nfl_core.stats"],
    packages=["nfl_core"],
    package_dir={"nfl_core": "."},
    install_requires=[
        "nflreadpy",
        "polars",
        "requests",
    ],
    python_requires=">=3.10",
)
