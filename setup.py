#!/usr/bin/env python
import setuptools

try:
   from setupext_janitor import janitor
   CleanCommand = janitor.CleanCommand
except ImportError:
   CleanCommand = None

cmd_classes = {}
if CleanCommand is not None:
   cmd_classes['clean'] = CleanCommand

def find_subpackages(package):
    packages = [package]
    for subpackage in setuptools.find_packages(package):
        packages.append("{0}.{1}".format(package, subpackage))
    return packages


setuptools.setup(name="azure_image_resizer",
    version="0.1",
    description="Azure Function image resizer with metadata file creation",
    url="",
    author="Mikael Weaver",
    packages=find_subpackages("azure_image_resizer"),
    license='MIT',
    setup_requires=['setupext_janitor'],
    cmdclass=cmd_classes,
    entry_points={
        # normal parameters, ie. console_scripts[]
        'distutils.commands': [
            ' clean = setupext_janitor.janitor:CleanCommand']
    })