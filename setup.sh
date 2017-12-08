#!/bin/sh

# setup buildbot
if [ ! -d master ]; then
    buildbot create-master -r master
    ln -s ../master.cfg master/master.cfg
    ln -s ../master_cfg_d master/master_cfg_d
fi
