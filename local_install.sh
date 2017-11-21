rm dist/*
./setup.py bdist_wheel
pip install $(find 'dist' -name 'licant*') --upgrade