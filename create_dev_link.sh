#!/bin/bash
cd /home/kp/Classes/cs397/plugin/deluge-1.3.6/deluge/scripts/localbff
mkdir temp
export PYTHONPATH=./temp
/usr/bin/python setup.py build develop --install-dir ./temp
cp ./temp/LocalBFF.egg-link /home/kp/.config/deluge/plugins
rm -fr ./temp
