#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import argparse
from base64 import b64encode
import random
import string
import json
import shutil

import yaml


def randstring(length=12):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def make_secrets():
    # create secrets file
    secrets_path = os.path.join('kubernetes','buildbot-secrets.yml')
    if not os.path.exists(secrets_path):
        with open(secrets_path,'wb') as f:
            yaml.dump({
                'apiVersion':'v1',
                'kind':'Secret',
                'metadata':{
                    'name':'cvmfs-buildbot',
                },
                'data':{
                    'worker_password': b64encode(randstring()),
                    'db_password': b64encode(randstring()),
                },
            }, f, default_flow_style=False)

def make_master_cfg():
    # create master.cfg file
    config_path = os.path.join('kubernetes','buildbot-master-cfg.json')
    config = {
        'master.cfg': open('master.cfg').read()
    }
    with open(config_path,'wb') as f:
        json.dump({
            'apiVersion':'v1',
            'kind':'ConfigMap',
            'metadata':{
                'name':'cvmfs-buildbot-master-cfg',
            },
            'data': config,
        }, f, sort_keys=True, indent=4, separators=(',',': '))

    config_path = os.path.join('kubernetes','buildbot-master-cfg-d.json')
    config = {}
    for c in os.listdir('master_cfg_d'):
        if not c.endswith('.py'):
            continue
        name = os.path.join('master_cfg_d',c)
        config[c] = open(name).read()
    with open(config_path,'wb') as f:
        json.dump({
            'apiVersion':'v1',
            'kind':'ConfigMap',
            'metadata':{
                'name':'cvmfs-buildbot-master-cfg-d',
            },
            'data': config,
        }, f, sort_keys=True, indent=4, separators=(',',': '))

def make_docker(name, push=False):
    # get current version
    version = None
    docker_path = os.path.join('docker_images',name)
    with open(os.path.join(docker_path,'Dockerfile')) as f:
        for line in f:
            if 'version=' in line:
                version = line.strip(' \n\r\\').split('=')[-1].strip('"')

    # check if docker image exists
    out = subprocess.check_output(['docker','images',
            '--filter','label=organization=icecube-buildbot',
            '--filter','label=name='+name,
            '--format','{{.Repository}} {{.Tag}}'])
    versions = set()
    if out:
        for l in out.split('\n'):
            if name in l:
                versions.add(l.split()[-1])
    if (version and version not in versions) or ((not version) and not versions):
        # build docker image
        if 'worker' in name:
            shutil.copy2('worker_buildbot.tac',
                         os.path.join(docker_path,'buildbot.tac'))
        elif 'master' in name:
            shutil.copy2('master_buildbot.tac',
                         os.path.join(docker_path,'buildbot.tac'))
        build_cmd = ['docker','build','--force-rm']
        push_cmd = []
        if version:
            build_cmd += ['-t','localhost:5000/icecube-buildbot-'+name+':'+version,
                          '-t','localhost:5000/icecube-buildbot-'+name+':latest']
            push_cmd += ['localhost:5000/icecube-buildbot-'+name+':'+version,
                          'localhost:5000/icecube-buildbot-'+name+':latest']
        else:
            build_cmd += ['-t','localhost:5000/icecube-buildbot-'+name+':latest']
            push_cmd += ['localhost:5000/icecube-buildbot-'+name+':latest']
        build_cmd += ['.']
        try:
            subprocess.check_call(build_cmd, cwd=docker_path)
            for img in push_cmd:
                subprocess.check_call(['docker','push',img], cwd=docker_path)
        except Exception,KeyboardInterrupt:
            out = subprocess.check_output(['docker','images',
                    '--filter','label=organization=icecube-buildbot',
                    '--filter','label=name='+name,
                    '--format','{{.ID}} {{.Repository}}'])
            if out:
                out = [l for l in out.split('\n') if name not in l]
                subprocess.call(['docker','image','rm',out[0].split()[0]])
            raise
        finally:
            os.remove(os.path.join(docker_path,'buildbot.tac'))

def make_workers():
    for name in os.listdir('docker_images'):
        if not name.startswith('worker'):
            continue

        # make docker image
        make_docker(name)

        # get labels
        container_name = 'localhost:5000/icecube-buildbot-'+name
        out = subprocess.check_output(['docker','inspect',container_name])
        config = json.loads(out)[0]['ContainerConfig']
        labels = config['Labels']
        version = labels['version'] if 'version' in labels else 'latest'
        cpus = int(labels['cpus']) if 'cpus' in labels else 1
        gpus = int(labels['gpus']) if 'gpus' in labels else 0
        memory = int(labels['memory']) if 'memory' in labels else 1000
        print(name,'cpus:',cpus,'gpus:',gpus,'memory:',memory)

        # create kubernetes worker json
        kubernetes_path = os.path.join('kubernetes',name+'.json')
        with open(kubernetes_path, 'w') as f:
            cfg = {
                'kind': 'Deployment', 
                'apiVersion': 'apps/v1beta1', 
                'metadata': {
                    'labels': {
                        'app': 'buildbot-worker',
                        'name': name
                    }, 
                    'name': name
                },
                'spec': {
                    'replicas': 1,  
                    'selector': {
                        'matchLabels': {
                            'app': 'buildbot-worker',
                            'name': name
                        }
                    },
                    'template': {
                        'spec': {
                            'containers': [{
                                'image': container_name+':'+version,
                                'imagePullPolicy': 'Always',
                                'name': name,
                                'resources': {
                                    'limits': {
                                        'cpu': str(cpus),
                                        'memory': str(memory)+"Mi",
                                        #'alpha.kubernetes.io/nvidia-gpu': gpus,
                                    },
                                },
                                'env': [
                                    {
                                        'name': 'BUILDMASTER', 
                                        'value': 'cvmfs-buildbot-worker',
                                    },{
                                        'name': 'BUILDMASTER_PORT', 
                                        'value': '9989',
                                    },{
                                        'name': 'WORKERNAME',
                                        'value': name.split('-',1)[-1],
                                    },{
                                        'name': 'WORKERPASS',
                                        'valueFrom': {
                                            'secretKeyRef': {
                                                'name': 'cvmfs-buildbot', 
                                                'key': 'worker_password'
                                            }
                                        },
                                    },
                                ],
                                'volumeMounts': [
                                    {
                                        'name': 'cvmfs-buildbot-worker-shared-storage',
                                        'mountPath': '/cvmfs',
                                    },
                                ],
                            }],
                            'ports': [],
                            'volumes': [{
                                'name': 'cvmfs-buildbot-worker-shared-storage',
                                'cephfs':{
                                    'monitors': ['10.254.81.20:6790','10.254.109.34:6790','10.254.34.31:6790'],
                                    'path': '/cvmfs',
                                    'user': 'admin',
                                    'secretRef': {
                                        'name': 'rook-admin'
                                    },
                                },
                            }],
                        }, 
                        'metadata': {
                            'labels': {
                                'app': 'buildbot-worker',
                                'name': name
                            }
                        }
                    },
                },
            }
            if 'stratum0' in name:
                cfg['spec']['template']['spec']['ports'].append({
                    'containerPort': 80,
                    'name': 'http',
                    'protocol': 'TCP',
                })
                cfg['spec']['template']['spec']['containers'][0]['volumeMounts'] = [
                    {
                        'name': 'cvmfs-buildbot-worker-shared-storage',
                        'mountPath': '/cvmfs-source',
                    },
                    {
                        'name': 'cvmfs-buildbot-stratum0-storage',
                        'mountPath': '/srv/cvmfs',
                    },
                    {
                        'name': 'cvmfs-buildbot-stratum0-tmp-storage',
                        'mountPath': '/var/spool/cvmfs',
                    },
                    {
                        'name': 'cvmfs-buildbot-stratum0-config-storage',
                        'mountPath': '/mnt/cvmfs_config',
                    },
                    {
                        'name': 'fuse',
                        'mountPath': '/dev/fuse',
                    },
                    {
                        'name': 'cgroup',
                        'mountPath': '/sys/fs/cgroup',
                        'readOnly': True,
                    },
                ]
                cfg['spec']['template']['spec']['volumes'].extend([
                    {
                        'name': 'cvmfs-buildbot-stratum0-storage',
                        'persistentVolumeClaim':{
                            'claimName': 'cvmfs-buildbot-stratum0-pv-claim',
                        },
                    },
                    {
                        'name': 'cvmfs-buildbot-stratum0-tmp-storage',
                        'persistentVolumeClaim':{
                            'claimName': 'cvmfs-buildbot-stratum0-spool-pv-claim',
                        },
                    },
                    {
                        'name': 'cvmfs-buildbot-stratum0-config-storage',
                        'persistentVolumeClaim':{
                            'claimName': 'cvmfs-buildbot-stratum0-config-pv-claim',
                        },
                    },
                    {
                        'name': 'fuse',
                        'hostPath':{
                            'path': '/dev/fuse',
                        },
                    },
                    {
                        'name': 'cgroup',
                        'hostPath':{
                            'path': '/sys/fs/cgroup',
                        },
                    },
                ])
                cfg['spec']['template']['spec']['containers'][0]['securityContext'] = {
                    'capabilities': {
                        'add': ['SYS_ADMIN'],
                    },
                    'privileged': True,
                }
            json.dump(cfg, f, sort_keys=True, indent=4, separators=(',',': '))
    

def main():
    parser = argparse.ArgumentParser(description='setup kubernetes')
    parser.add_argument('--push',action='store_true',default=False,help='push to docker registry')
    args = parser.parse_args()

    make_secrets()
    make_master_cfg()
    make_docker('master-cvmfs',push=args.push)
    make_workers()

if __name__ == '__main__':
    main()
