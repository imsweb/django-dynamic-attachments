from setuptools import setup, find_packages
from attachments.version import __version__

setup(
    name='attachments',
    version=__version__,
    description='A Django application for handling file uploads and attaching them to arbitrary models.',
    author='Dan Watson',
    author_email='watsond@imsweb.com',
    url='http://imsweb.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)
