from setuptools import setup, find_namespace_packages

setup(
    name="mancer",
    version="0.1.6",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    description="Multisystem Programmable Engine - A framework for programmable system automation with bash and PowerShell support",
    author="Kacper Paczos",
    author_email="kacperpaczos2024@proton.me",
    python_requires=">=3.8",
    license="MIT",
)
