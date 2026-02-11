"""
Setup configuration for SKONG package
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read version from package
version = {}
with open(os.path.join(this_directory, "skong", "__init__.py"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="skong",
    version=version.get("__version__", "0.1.0"),
    author="Guglielmo Grillo",
    author_email="",
    description="System for Keeping Organized Numerical Goals - A tool to ease the use of UNITN HPC (PBS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NerusSkyhigh/SKONG",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.7",
    install_requires=[
        # Add dependencies here as needed
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "skong=skong.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
