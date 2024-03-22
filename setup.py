from setuptools import find_packages, setup

import attachments
import os
import re


def get_installs():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as fp:
        return [
            line.rstrip() for line in fp.readlines() if not re.match(r"(\n.*)", line) and not re.match(r"(#.*)", line)
        ]


setup(
    name='django-dynamic-attachments',
    version=attachments.__version__,
    description='A Django application for handling file uploads and attaching them to arbitrary models.',
    author='Dan Watson',
    author_email='watsond@imsweb.com',
    url='https://github.com/imsweb/django-dynamic-attachments',
    license='BSD',
    packages=find_packages(exclude=('testapp',)),
    include_package_data=True,
    install_requires=get_installs(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
