"""
Flabric
--------------

Simple sysadmin using Fabric and Cuisine


Links
`````

* `development version
  <https://github.com/mattupstate/flabric/raw/develop#egg=Flabric-dev>`_

"""
import os
from setuptools import setup

def fullsplit(path, result=None):
    """Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages, data_files = [], []
root_dir = os.path.dirname(__file__)

if root_dir != '':
    os.chdir(root_dir)
    
flabric_dir = 'flabric'

for dirpath, dirnames, filenames in os.walk(flabric_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
        
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
        
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='Flabric',
    version='0.1.0',
    url='https://github.com/mattupstate/flabric',
    license='MIT',
    author='Matthew Wright',
    author_email='matt@nobien.net',
    description='Simple sysadmin using Fabric and Cuisine',
    long_description=__doc__,
    packages=packages,
    data_files=data_files,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'cuisine'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)