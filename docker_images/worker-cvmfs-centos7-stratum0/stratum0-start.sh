#!/bin/sh

REPO=icecube.opensciencegrid.org

# set up cvmfs_config
if [ -d /mnt/cvmfs_config ]; then
    if [ ! -L /etc/cvmfs ]; then
        rsync -a --exclude '*icecube*' /etc/cvmfs/ /mnt/cvmfs_config/
        rm -rf /etc/cvmfs
        ln -s /etc/cvmfs /mnt/cvmfs_config
    fi
fi

# make cvmfs fs if not already existing
if [ ! -d /etc/cvmfs/repositories.d/$REPO ]; then
    cvmfs_server mkfs -o buildbot $REPO

    python - <<EOF
import os
path = "server.conf"
newdata = {
    'CVMFS_IGNORE_XDIR_HARDLINKS':'true',
    'CVMFS_GENERATE_LEGACY_BULK_CHUNKS':'false',
    'CVMFS_AUTOCATALOGS':'true',
    'CVMFS_AUTO_TAG':'false',
    'CVMFS_GARBAGE_COLLECTION':'true',
}
lines = open(path).read().split('\n')
with open(path,'w') as f:
    for l in lines:
        if '=' in l:
            parts = l.split('=',1)
            k = parts[0].strip()
            if k in newdata:
                l = k+'='+newdata[k]
        f.write(l+'\n')
EOF

fi
