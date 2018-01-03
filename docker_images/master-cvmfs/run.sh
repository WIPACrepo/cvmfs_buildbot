#/bin/bash

# copy cfgmap python files, because we can't use them directly
mkdir /data/master_cfg_d
cp /buildbot/master_cfg_d/*.py /data/master_cfg_d/
export PYTHONPATH=/data

# update database if necessary
buildbot upgrade-master /usr/share/buildbot

# run
twistd -ny /usr/share/buildbot/buildbot.tac