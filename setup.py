from setuptools import find_packages, setup

setup(
    name="gc_registry",
    version="0.0.1",
    python_requires=">=3.11,<4",
    description="FEA EnergyTag Granular Certificate Demonstration Registry Platform",
    author="Connor Galbraith",
    author_email="connor@futureenergy.associates",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
