from setuptools import find_packages, setup

import attachments


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
    install_requires=[
        'pyclamd',
        'python-magic;platform_system!="Windows"',
        'python-magic-bin;platform_system=="Windows"',
    ],
    extras_require={
        "bootstrap": ["ims-bootstrap>=5.0,<6.0"],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
