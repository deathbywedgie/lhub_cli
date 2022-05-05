from setuptools import setup, find_packages

VERSION = '0.1.0.1'

setup(
    name="lhub_cli",
    version=VERSION,
    author="Chad Roberts",
    author_email="chad@logichub.com",
    description="LogicHub CLI",
    long_description="A Python package for interacting with LogicHub via shell commands",
    packages=find_packages(),
    install_requires=[
        "lhub ~= 0.2.0",
        "configobj >= 5.0.6",
        "dataclasses_json >= 0.5.6",
        "rsa >= 4.8",
        "requests",
        "tabulate",
        "colorama",
        "progressbar2",  # Only used in sample scripts for now, and imported not as "progressbar2" but just "progressbar"
    ],
    keywords=["python", "lhub", "LogicHub", "api", "security", "cli"],

    url="https://github.com/deathbywedgie/lhub_cli",
    project_urls={
        "Bug Tracker": "https://github.com/deathbywedgie/lhub_cli/issues",
    },

    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.10",
        "Natural Language :: English",
    ]
)
