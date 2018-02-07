./make.sh
echo "PYTHON3 install"
python3 -m pip install $(find 'dist' -name 'licant*py3*') --upgrade
echo "PYTHON2 install"
python -m pip install $(find 'dist' -name 'licant*py2*') --upgrade