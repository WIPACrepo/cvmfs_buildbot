#!/bin/sh

# setup python env
if [ ! -d python_env ]; then
    virtualenv python_env
fi
. python_env/bin/activate
pip install -r requirements.txt

# setup singularity images
if [ ! -d singularity_images ]; then
    mkdir singularity_images
fi
python setup_singularity.py

# setup buildbot
if [ ! -d master ]; then
    buildbot create-master -r master
    ln -s ../master.cfg master/master.cfg
fi
