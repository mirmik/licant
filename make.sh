rm dist/*
#echo "PYTHON2 make"
#python2 ./setup.py bdist_wheel
echo "PYTHON2.7 make"
python2.7 ./setup.py bdist_wheel
echo "PYTHON3.6 make"
python3.6 ./setup.py bdist_wheel
#echo "PYTHON3.5 make"
#python3.5 ./setup.py bdist_wheel
#echo "PYTHON3.5m make"
#python3.5m ./setup.py bdist_wheel