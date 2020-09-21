import setuptools
import pathlib
from subs2cia import __version__

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
long_description = (HERE / "README.md").read_text()

setuptools.setup(
    name="subs2cia",
    version=__version__,
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
    python_requires='>=3.7',
    install_requires=[
        "ffmpeg-python",
        "pycountry",
        "pysubs2"
    ],
    entry_points={
        # create a cli command called 'subs2cia' which runs the main() function in subs2cia.cli
        'console_scripts': ['subs2cia=subs2cia.cli:main', 'subzipper=subs2cia.cli:subzipper_main']
    }
)