rm dist/*
./setup.py bdist_wheel
python3 -m pip install $(find 'dist' -name 'licant*') --upgrade