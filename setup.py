from setuptools import setup


def get_required_packages(fp: str = "requirements.txt"):
    with open(fp) as f:
        required = f.read().splitlines()

    return required


setup(
    name="gc_registry",
    version="0.0.1",
    python_requires=">=3.10",
    description="FEA EnergyTag Granular Certificate Demonstration Registry Platform",
    author="Connor Galbraith",
    author_email="connor@futureenergy.associates",
    packages=["energytag"],
    install_requires=get_required_packages(),
)
