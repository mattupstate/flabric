"""
Flabric
--------------

Flabric aims to make the task of deploying a Flask application to EC2 relatively simple
using nginx, uWSGI, and supervisord.


Links
`````

* `development version
  <https://github.com/mattupstate/flabric/raw/develop#egg=Flabric-dev>`_

"""

from setuptools import setup

setup(
    name='Flabric',
    version='0.1.0',
    url='https://github.com/mattupstate/flabric',
    license='MIT',
    author='Matthew Wright',
    author_email='matt@nobien.net',
    description='Simple sysadmin of Flask apps on EC2',
    long_description=__doc__,
    packages=[
        'flabric',
        'flabric.cookbooks'
    ],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'fabric',
        'cuisine',
        'boto'
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