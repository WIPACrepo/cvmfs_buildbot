#/bin/bash
if [ ! -e /data/state.sqlite ]; then
    # re-create /data
    rm -rf /data/*
    buildbot create-master /data
    rm -f buildbot.tac
fi
rm -rf /data/master_cfg_d /data/twistd.pid
# copy cfgmap python files, because we can't use them directly
mkdir /data/master_cfg_d
cp /buildbot/master_cfg_d/*.py /data/master_cfg_d/
export PYTHONPATH=/data
# run 
twistd -ny /usr/share/buildbot/buildbot.tac