from setuptools import setup, find_packages

VERSION = '0.0.3'

setup(
    name="lhub_cli",
    version=VERSION,
    author="Chad Roberts",
    author_email="chad@logichub.com",
    description="LogicHub CLI",
    long_description="A Python package for interacting with LogicHub via shell commands",
    packages=find_packages(),
    install_requires=[
        "requests"
    ],
    keywords=["python", "lhub", "LogicHub"],

    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Natural Language :: English",
    ]
)
