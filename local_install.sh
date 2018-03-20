./make.sh
#echo "PYTHON3 install"
#sudo -H python3 -m pip install $(find 'dist' -name 'licant*py3*') --upgrade

echo "PIP2 install"
sudo -H python2 -m pip install $(find 'dist' -name 'licant*py2*') --upgrade
echo "PIP3 install"
sudo -H python3 -m pip install $(find 'dist' -name 'licant*py3*') --upgrade
echo "PIP3 install"
sudo -H python3.5 -m pip install $(find 'dist' -name 'licant*py3*') --upgrade
#echo "PYTHON2 install"
#sudo -H python -m pip install $(find 'dist' -name 'licant*py2*') --upgrade