from __future__ import print_function

import os
import json

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED,FAILURE

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]


def setup(cfg):

    ####### WORKERS

    workername = 'cvmfs-stratum0'
    cfg['workers'][prefix] = worker.Worker(
        workername, os.environ['WORKER_PASSWORD'],
        max_builds=1,
        properties={},
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

    def BuildFailed(step):
        return step.build.result == FAILURE
    def BuildPassed(step):
        return step.build.result == SUCCESS

    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(
        name='open transaction',
        command=['cvmfs_server','transaction','icecube.opensciencegrid.org'],
        haltOnFailure=True,
    ))
    factory.addStep(steps.ShellCommand(
        name='rsync',
        command=[
            'cvmfs_rsync',
            util.Interpolate('/cvmfs-source/icecube.opensciencegrid.org/$(prop:variant)s'),
            util.Interpolate('/cvmfs/icecube.opensciencegrid.org/$(prop:variant)s'),
        ],
        haltOnFailure=True,
        doStepIf=BuildPassed,
    ))
    factory.addStep(steps.ShellCommand(
        name='publish transaction',
        command=['cvmfs_server','publish','icecube.opensciencegrid.org'],
        haltOnFailure=True,
        doStepIf=BuildPassed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))
    factory.addStep(steps.ShellCommand(
        name='abort transaction',
        command=['cvmfs_server','abort','-f','icecube.opensciencegrid.org'],
        haltOnFailure=True,
        doStepIf=BuildFailed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))

    cfg['builders'][prefix+'_builder'] = util.BuilderConfig(
        name=prefix+'_builder',
        workername=workername,
        factory=factory,
        properties={},
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive')
        ],
    )


    ####### SCHEDULERS

    cfg['schedulers'][prefix+'-force'] = schedulers.ForceScheduler(
        name="publish",
        builderNames=list(cfg['builders'].keys()),
        properties=[
            util.StringParameter(name="variant",
                                 label="Variant:",
                                 default="", size=80),
        ],
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)