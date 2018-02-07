rm dist/*
echo "PYTHON3 make"
python ./setup.py bdist_wheel
echo "PYTHON2 make"
python3 ./setup.py bdist_wheel