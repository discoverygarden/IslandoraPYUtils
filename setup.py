'''
Created on Apr 18, 2011

Setup script for isladoraUtils

@author: William Panting
'''
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
      name='islandoraUtils',
      version='0.1',
      description='A Package meant to assist Islandora developers',
      author='William Panting',
      author_email='will@discoverygarden.ca',
      license = "GPL",
      packages=find_packages(),
      package_dir={"islandoraUtils" : "islandoraUtils"},
      package_data={"islandoraUtils" : ["__resources/*.xslt"]},
      long_description=read('README'),
      install_requires=['setuptools','lxml']
      )
