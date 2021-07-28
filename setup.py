import setuptools
import pathlib
import os

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
long_description = (HERE / "README.md").read_text()


# from pip's setup.py:
def read(rel_path):
    # type: (str) -> str
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


# from pip's setup.py:
def get_version(rel_path):
    # type: (str) -> str
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="subs2cia",
    version=get_version("subs2cia/__init__.py"),
    license='MIT',
    author="Daniel Xing",
    author_email="danielxing97@gmail.com",
    description="A subtitle-based multimedia extractor and compressor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dxing97/subs2cia",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "ffmpeg-python",
        "pycountry",
        "pysubs2",
        "tqdm",
        "pandas", "tqdm", "gevent", "colorlog"
    ],
    entry_points={
        # create a cli command called 'subs2cia' which runs the main() function in subs2cia.cli
        'console_scripts': ['subs2cia=subs2cia.cli:main', 'subzipper=subs2cia.cli:subzipper_main']
    }
)