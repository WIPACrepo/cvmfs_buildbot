#!/usr/bin/env python

import os
import shutil
import subprocess
from copy import deepcopy
import json
import getpass

default_cfg = {
    'image':{
        'size': 4096,
    },
    'postinstall':[
        'mkdir /cvmfs',
    ],
}

def import_config(cfg_path):
    ret = {}
    with open(cfg_path) as f:
        ret = json.load(f)
    for s in default_cfg:
        if s in ret:
            if isinstance(default_cfg[s],dict):
                ret[s].update(default_cfg[s])
            elif isinstance(default_cfg[s],list):
                ret[s].extend(default_cfg[s])
        else:
            ret[s] = deepcopy(default_cfg[s])
    # validate
    ret['image']['docker_image']
    return ret

username = getpass.getuser()

for cfg in os.listdir('configs'):
    cfg_path = os.path.join('configs',cfg)
    config = import_config(cfg_path)
    img_path = os.path.join('singularity_images',cfg.replace('json','img'))
    if not os.path.exists(img_path):
        print('bootstrapping image:',img_path)
        try:
            subprocess.check_call(['sudo', 'singularity', 'create',
                                   '--size', str(config['image']['size']),
                                   img_path
                                  ])
            subprocess.check_call(['sudo', 'chown', username, img_path])
            subprocess.check_call(['sudo', 'singularity', 'import', img_path,
                                   'docker://'+config['image']['docker_image']
                                  ])
            for line in config['postinstall']:
                cmd = 'sudo singularity exec --writable '+img_path+' '+line
                subprocess.check_call(cmd, shell=True)
        except:
            if os.path.exists(img_path):
                os.remove(img_path)
            raise
