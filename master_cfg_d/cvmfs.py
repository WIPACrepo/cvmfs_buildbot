from __future__ import print_function

import os
import json

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]

worker_cfgs = {
    'cvmfs-centos7-build': 'worker-cvmfs-centos7-build',
}

def setup(cfg):

    ####### WORKERS

    for name in worker_cfgs:
        workername = 'cvmfs-centos7-build'
        cfg['workers'][name] = worker.Worker(
            name, os.environ['WORKER_PASSWORD'],
            max_builds=1,
            properties={
                'CPUS': '4',
                'MEMORY': '8000',
            },
        )

    ####### CHANGESOURCES

    cfg['change_source']['cvmfs'] = changes.GitPoller(
        'git://github.com/WIPACrepo/cvmfs.git',
        workdir=prefix+'-cvmfs-gitpoller-workdir', branch='master',
        category=prefix,
        pollinterval=300,
    )


    ####### BUILDERS

    """ for nightly
    def isImportant(change):
        try:
            if not (os.path.exists(path) and os.listdir(path)):
                return True # needs rebuilding
            include = ['setup.cfg','setup.py','requirements.txt']
            for f in change.files:
                if f in include:
                    return True
            return False
        except:
            raise
            return True

    class SetupCVMFS(steps.BuildStep):
        def run(self):
            changes = util.Property('changes')
            if isImportant(changes):
                # create a ShellCommand for each stage and add them to the build
                self.build.addStepsAfterCurrentStep([
                ])
                return SUCCESS
            return SKIPPED
    """

    factory = util.BuildFactory()
    factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    factory.addStep(steps.ShellCommand(
        name='build cvmfs',
        command=[
            'python', 'builders/build.py',
            '--src', 'icecube.opensciencegrid.org',
            '--dest', '/cvmfs/icecube.opensciencegrid.org',
            '--variant', util.Property('variant'),
        ],
        env={
            'CPUS': util.Property('CPUS', default='1'),
            'MEMORY': util.Property('MEMORY', default='1'),
        },
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive')
        ],
    ))

    
    for name in worker_cfgs:
        cfg['builders'][name+'_builder'] = util.BuilderConfig(
            name=name+'_builder',
            workername=name,
            factory=factory,
            properties={},
        )


    ####### SCHEDULERS

    variants = ['py2_v3_base','py2_v3_metaproject','iceprod']
    for v in variants:
        cfg['schedulers'][prefix+'-'+v] = schedulers.SingleBranchScheduler(
            name=prefix+'-'+v,
            change_filter=util.ChangeFilter(category=prefix),
            treeStableTimer=None,
            builderNames=list(cfg['builders'].keys()),
            properties={'variant':v},
        )
    cfg['schedulers'][prefix+'-force'] = schedulers.ForceScheduler(
        name=prefix+"-force",
        builderNames=list(cfg['builders'].keys()),
        properties=[
            util.StringParameter(name="variant",
                                 label="Variant:",
                                 default="", size=80),
        ],
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
