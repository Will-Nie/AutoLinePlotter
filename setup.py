import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='AutoLinePlotter',
    version='0.0.1',
    packages=setuptools.find_packages(),
    url='https://github.com/Will-Nie/AutoLinePlotter',
    license='Apache License, Version 2.0',
    author='WillNie; Weiyuhong',
    author_email='nieyunpengwill@hotmail.com',
    description='This repo support auto line plot for multi-seed event file from TensorBoard',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['numpy','tensorboard','matplotlib','seaborn','pandas','typing'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

