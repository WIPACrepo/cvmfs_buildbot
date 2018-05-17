#!/bin/sh

REPO=icecube.opensciencegrid.org

# set up cvmfs_config
if [ -d /mnt/cvmfs_config ]; then
    rsync -a /mnt/cvmfs_config/keys/ /etc/cvmfs/keys/
fi

# always import cvmfs on startup
if [ -d /etc/cvmfs/repositories.d/$REPO ]; then
    rm -rf /etc/cvmfs/repositories.d/$REPO
fi

# wait for httpd to start
sleep 2

rm -rf /var/spool/cvmfs/$REPO
cvmfs_server import -o buildbot $REPO

if [ $? == 0 ]; then
    python - <<EOF
import os
path = "/etc/cvmfs/repositories.d/$REPO/server.conf"
newdata = {
'CVMFS_IGNORE_XDIR_HARDLINKS':'true',
'CVMFS_GENERATE_LEGACY_BULK_CHUNKS':'false',
'CVMFS_AUTOCATALOGS':'true',
'CVMFS_AUTO_TAG':'false',
'CVMFS_GARBAGE_COLLECTION':'true',
'CVMFS_FILE_MBYTE_LIMIT':2048,
}
lines = open(path).read().split('\n')
with open(path,'w') as f:
    for l in lines:
        if '=' in l:
            parts = l.split('=',1)
            k = parts[0].strip()
            if k in newdata:
                continue
        f.write(l+'\n')
    for k in newdata:
        f.write(k+'='+newdata[k]+'\n')
EOF
else
    rm -rf /etc/cvmfs/repositories.d/$REPO
    exit 1
fi
