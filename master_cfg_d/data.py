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

    # GCD sync
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

    # test-data sync
    build_factory = util.BuildFactory()
    build_factory.addStep(steps.ShellCommand(
        name='copy test-data',
        command=['rsync','-vrlpt','--delete','code.icecube.wisc.edu::Offline/test-data/releases/V00-00-01/','/cvmfs/icecube.opensciencegrid.org/data/i3-test-data/'],
        workdir='/cvmfs/icecube.opensciencegrid.org/data',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))
    build_factory.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': 'data/i3-test-data',
        }
    ))

    cfg['builders']['test_data_builder'] = util.BuilderConfig(
        name='test_data_builder',
        workername='cvmfs-centos7-build',
        factory=build_factory,
        properties={},
    )


    ####### SCHEDULERS
    cfg['schedulers'][prefix+'-gcd-force'] = schedulers.ForceScheduler(
        name=prefix+"-gcd-force",
        builderNames=['gcd_builder'],
        properties=[],
    )
    cfg['schedulers'][prefix+'-test-data-force'] = schedulers.ForceScheduler(
        name=prefix+"-test-data-force",
        builderNames=['test_data_builder'],
        properties=[],
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
