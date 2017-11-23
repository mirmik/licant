rm dist/*
./setup.py bdist_wheel
sudo pip install $(find 'dist' -name 'licant*') --upgrade