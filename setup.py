from setuptools import find_namespace_packages, setup

setup(
    name="mancer",
    version="0.7.1",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    description="Programmable automation engine - execute commands on any platform (Linux/Windows/macOS) locally or remotely through one Python interface",
    author="Kacper Paczos",
    author_email="kacperpaczos2024@proton.me",
    python_requires=">=3.8",
    license="MIT",
)
