from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="MLOps Project 2",
    version="0.1",
    author="Karthik",
    packages=find_packages(),
    install_requires = requirements,
)