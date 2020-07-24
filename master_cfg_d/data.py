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

    # new test-data sync
    build_factory = util.BuildFactory()
    build_factory.addStep(steps.ShellCommand(
        name='copy test-data',
        command=['rsync','-vrlpt','--delete','code.icecube.wisc.edu::Offline/test-data/','/cvmfs/icecube.opensciencegrid.org/data/i3-test-data-svn/'],
        workdir='/cvmfs/icecube.opensciencegrid.org/data',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))
    build_factory.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': 'data/i3-test-data-svn',
        }
    ))

    cfg['builders']['test_data_svn_builder'] = util.BuilderConfig(
        name='test_data_svn_builder',
        workername='cvmfs-centos7-build',
        factory=build_factory,
        properties={},
    )
    

    # L3 LE retro tables sync
    build_factory = util.BuildFactory()
    build_factory.addStep(steps.ShellCommand(
        name='copy tables',
        command=['wget','-nH','--cut-dirs','6','-P','retro','-np','-nc','-r','-l','4','-A','*.npy','https://icecube:skua@convey.icecube.wisc.edu/data/ana/reconstruction/2019/retro/tables/'],
        workdir='/cvmfs/icecube.opensciencegrid.org/data/photon-tables/',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))
    build_factory.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': 'data/photon-tables',
        }
    ))

    cfg['builders']['le_retro_tables'] = util.BuilderConfig(
        name='le_retro_tables',
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
    cfg['schedulers'][prefix+'-gcd-nightly'] = schedulers.Nightly(
        name=prefix+"-gcd-nightly",
        builderNames=['gcd_builder'],
        properties={},
        hour=2, minute=45,
    )
    cfg['schedulers'][prefix+'-test-data-force'] = schedulers.ForceScheduler(
        name=prefix+"-test-data-force",
        builderNames=['test_data_builder'],
        properties=[],
    )
    cfg['schedulers'][prefix+'-test-data-svn-force'] = schedulers.ForceScheduler(
        name=prefix+"-test-data-svn-force",
        builderNames=['test_data_svn_builder'],
        properties=[],
    )
    cfg['schedulers'][prefix+'-test-data-svn-nightly'] = schedulers.Nightly(
        name=prefix+"-test-data-svn-nightly",
        builderNames=['test_data_svn_builder'],
        properties={},
        hour=2, minute=0,
    )
    cfg['schedulers'][prefix+'-le_retro_tables-force'] = schedulers.ForceScheduler(
        name=prefix+"-le_retro_tables-force",
        builderNames=['le_retro_tables'],
        properties=[],
    )
    cfg['schedulers'][prefix+'-le_retro_tables-nightly'] = schedulers.Nightly(
        name=prefix+"-le_retro_tables-nightly",
        builderNames=['le_retro_tables'],
        properties={},
        hour=2, minute=30,
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
