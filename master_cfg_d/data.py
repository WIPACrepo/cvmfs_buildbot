from __future__ import print_function

import os
import json
import random

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]


def setup(cfg):

    ####### WORKERS

    ####### CHANGESOURCES

    ####### BUILDERS
    
    build_factory = util.BuildFactory()
    build_factory.addStep(steps.ShellCommand(
        name='copy GCD',
        command=['wget','-nd','-nc','-r','-l','1','-A','Geo*','http://prod-exe.icecube.wisc.edu/GCD/'],
        workdir='/cvmfs/icecube.opensciencegrid.org/data/GCD',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))
    build_factory.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': 'data/GCD',
        }
    ))


    cfg['builders']['gcd_builder'] = util.BuilderConfig(
        name='gcd_builder',
        workername='cvmfs-centos7-build',
        factory=build_factory,
        properties={},
    )

    ####### SCHEDULERS
    cfg['schedulers'][prefix+'-force'] = schedulers.ForceScheduler(
        name=prefix+"-force",
        builderNames=['gcd_builder'],
        properties=[],
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
