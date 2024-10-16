import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="gd2score",
    version="1.0.0",
    author="John A. Brewer",
    author_email="brewerja@gmail.com",
    description=(
        "A tool to automatically create an SVG Allen Scorecard from "
        "MLB.com Stats API play by play data."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brewerja/gd2score",
    keywords="baseball mlb",
    packages=setuptools.find_packages(exclude=["tests"]),
    install_requires=["svgwrite"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3.0"
        "Operating System :: OS Independent",
    ],
)
