#!/usr/bin/env python

from __future__ import print_function

import os
import shutil
import tempfile
import subprocess
import time
import json

def docker_stop(name):
    for line in subprocess.check_output(['docker','ps','--filter=id='+name,'--no-trunc','-q']).split('\n'):
        if line == name:
            subprocess.call(['docker','stop',line])

def main():
    master_id = ''
    workers = {}

    buildcache = os.path.join(os.getcwd(),'buildcache')
    if not os.path.exists(buildcache):
        os.mkdir(buildcache)
    master_data = os.path.join(buildcache,'master')
    if not os.path.exists(master_data):
        os.mkdir(master_data)
    cvmfs_data = os.path.join(buildcache,'cvmfs')
    if not os.path.exists(cvmfs_data):
        os.mkdir(cvmfs_data)
    try:
        master_id = subprocess.check_output(['docker','run','-d','--rm',
                '-p','8010:8010',
                '-v',os.getcwd()+':/buildbot:ro',
                '-v',master_data+':/data',
                '-e','WORKER_PASSWORD=pass',
                '-e','BUILDBOT_MASTER_URL=http://localhost:8010/',
                'icecube-buildbot/master-cvmfs']).strip()
        time.sleep(.1)
        print('Master started at',master_id[:12])

        # get master ip address
        data = json.loads(subprocess.check_output(['docker','inspect',master_id]))[0]
        master_ip = data['NetworkSettings']['IPAddress']

        for name in os.listdir('docker_images'):
            if name.startswith('worker'):
                name = name.split('-',1)[1]
                w = subprocess.check_output(['docker','run','-d','--rm',
                    '-v',cvmfs_data+':/cvmfs',
                    '-e','WORKERPASS=pass',
                    '-e','BUILDMASTER='+master_ip,
                    '-e','BUILDMASTER_PORT=9989',
                    '-e','WORKERNAME='+name,
                    'icecube-buildbot/worker-'+name]).strip()
                workers[name] = w
                time.sleep(.1)
                print('Worker',name,'started at',w[:12])

        try:
            time.sleep(1000000000000)
        except KeyboardInterrupt:
            pass

    finally:
        print('shutting down')
        docker_stop(master_id)
        for name in workers:
            docker_stop(workers[name])

if __name__ == '__main__':
    main()
