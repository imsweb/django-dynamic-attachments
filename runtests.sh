#!/bin/bash

if [ ! -d pybin ]; then
    virtualenv-2.7 pybin
fi

cd tests

../pybin/bin/pip install -r requirements.txt
../pybin/bin/python manage.py test_coverage

cd ..

rm -f coverage.zip
cd coverage_html
zip -r ../coverage.zip *
