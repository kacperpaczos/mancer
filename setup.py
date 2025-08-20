from setuptools import setup, find_namespace_packages

setup(
    name="mancer",
    version="0.1.4",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    description="Framework DDD dla komend systemowych",
    author="Kacper Paczos",
    author_email="kacperpaczos2024@proton.me",
    python_requires=">=3.8",
    license="MIT",
)
