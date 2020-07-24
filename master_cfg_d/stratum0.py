from __future__ import print_function

import os
import json

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED,FAILURE

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]


def setup(cfg):

    ####### WORKERS

    workername = 'cvmfs-centos7-stratum0'
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
        return step.build.results == FAILURE
    def BuildPassed(step):
        return step.build.results == SUCCESS

    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(
        name='open transaction',
        command=['cvmfs_server','transaction','icecube.opensciencegrid.org'],
        haltOnFailure=True,
    ))
    @util.renderer
    def makeCommandRsync(props):
        src_path = os.path.join('icecube.opensciencegrid.org',
                                str(props.getProperty('variant')))
        dest_path = os.path.dirname(src_path)
        command = [
            'cvmfs_rsync','-ai','--delete',
            os.path.join('/cvmfs-source',src_path),
            os.path.join('/cvmfs',dest_path)+'/',
        ]
        return command
    factory.addStep(steps.ShellCommand(
        name='rsync',
        command=makeCommandRsync,
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
    ))
    factory.addStep(steps.ShellCommand(
        name='publish transaction',
        command=['cvmfs_server','publish','icecube.opensciencegrid.org'],
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))
    factory.addStep(steps.ShellCommand(
        name='abort transaction',
        command=['cvmfs_server','abort','-f','icecube.opensciencegrid.org'],
        alwaysRun=True,
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
            cfg.locks['cvmfs_shared'].access('exclusive'),
            cfg.locks['cvmfs_publish'].access('exclusive')
        ],
        collapseRequests=True,
    )
    
    # ARA publish
    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(
        name='open transaction',
        command=['cvmfs_server','transaction','ara.opensciencegrid.org'],
        haltOnFailure=True,
    ))
    @util.renderer
    def makeCommandRsyncARA(props):
        src_path = os.path.join('ara.opensciencegrid.org',
                                str(props.getProperty('path')))
        dest_path = os.path.dirname(src_path)
        command = [
            'cvmfs_rsync','-ai','--delete',
            os.path.join('/cvmfs-source',src_path),
            os.path.join('/cvmfs',dest_path)+'/',
        ]
        return command
    factory.addStep(steps.ShellCommand(
        name='rsync',
        command=makeCommandRsyncARA,
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
    ))
    factory.addStep(steps.ShellCommand(
        name='publish transaction',
        command=['cvmfs_server','publish','ara.opensciencegrid.org'],
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))
    factory.addStep(steps.ShellCommand(
        name='abort transaction',
        command=['cvmfs_server','abort','-f','ara.opensciencegrid.org'],
        alwaysRun=True,
        haltOnFailure=True,
        doStepIf=BuildFailed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))

    cfg['builders'][prefix+'_ara_builder'] = util.BuilderConfig(
        name=prefix+'_ara_builder',
        workername=workername,
        factory=factory,
        properties={},
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive'),
            cfg.locks['cvmfs_publish'].access('exclusive')
        ],
        collapseRequests=True,
    )

    # download whitelists
    factory_whitelist = util.BuildFactory()
    factory_whitelist.addStep(steps.ShellCommand(
        name='resign IceCube whitelist',
        command='cd /srv/cvmfs/icecube.opensciencegrid.org && rm -f .cvmfswhitelist.new && wget -qO .cvmfswhitelist.new http://oasis.opensciencegrid.org/cvmfs/icecube.opensciencegrid.org/.cvmfswhitelist && mv -f .cvmfswhitelist.new .cvmfswhitelist',
        haltOnFailure=True,
    ))
    factory_whitelist.addStep(steps.ShellCommand(
        name='resign ARA whitelist',
        command='cd /srv/cvmfs/ara.opensciencegrid.org && rm -f .cvmfswhitelist.new && wget -qO .cvmfswhitelist.new http://oasis.opensciencegrid.org/cvmfs/ara.opensciencegrid.org/.cvmfswhitelist && mv -f .cvmfswhitelist.new .cvmfswhitelist',
        haltOnFailure=True,
    ))

    cfg['builders'][prefix+'_whitelist'] = util.BuilderConfig(
        name=prefix+'_whitelist',
        workername=workername,
        factory=factory_whitelist,
        properties={},
        locks=[
            cfg.locks['cvmfs_publish'].access('exclusive')
        ],
        collapseRequests=True,
    )

    # user cvmfs
    factory_user_rsync = util.BuildFactory()
    factory_user_rsync.addStep(steps.ShellCommand(
        name='open transaction',
        command=['cvmfs_server','transaction','icecube.opensciencegrid.org'],
        haltOnFailure=True,
    ))
    factory_user_rsync.addStep(steps.ShellCommand(
        name='rsync',
        command=[
            'cvmfs_rsync','-ai','--delete',
            'rsync://nfs-6.icecube.wisc.edu/pcvmfs/',
            '/cvmfs/icecube.opensciencegrid.org/users/',
        ],
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
    ))
    factory_user_rsync.addStep(steps.ShellCommand(
        name='publish transaction',
        command=['cvmfs_server','publish','icecube.opensciencegrid.org'],
        timeout=7200, # 2 hours
        haltOnFailure=True,
        doStepIf=BuildPassed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))
    factory_user_rsync.addStep(steps.ShellCommand(
        name='abort transaction',
        command=['cvmfs_server','abort','-f','icecube.opensciencegrid.org'],
        alwaysRun=True,
        haltOnFailure=True,
        doStepIf=BuildFailed,
        hideStepIf=lambda results, s: results==SKIPPED,
    ))

    cfg['builders'][prefix+'_user_rsync'] = util.BuilderConfig(
        name=prefix+'_user_rsync',
        workername=workername,
        factory=factory_user_rsync,
        properties={},
        locks=[
            cfg.locks['cvmfs_publish'].access('exclusive')
        ],
        collapseRequests=True,
    )

    # backup of IceCube
    factory_backup = util.BuildFactory()
    factory_backup.addStep(steps.ShellCommand(
        name='rsync',
        command=['rsync','-ai','--delete','/cvmfs-source/icecube.opensciencegrid.org','rsync://nfs-5.icecube.wisc.edu/cvmfs/'],
        timeout=14400, # 4 hours
        haltOnFailure=True,
    ))

    cfg['builders'][prefix+'_backup'] = util.BuilderConfig(
        name=prefix+'_backup',
        workername=workername,
        factory=factory_backup,
        properties={},
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive')
        ],
        collapseRequests=True,
    )

    ####### SCHEDULERS

    cfg['schedulers']['publish-force'] = schedulers.ForceScheduler(
        name="publish-force",
        builderNames=[prefix+'_builder'],
        properties=[
            util.StringParameter(name="variant",
                                 label="Variant:",
                                 default="", size=80),
        ],
    )
    cfg['schedulers']['publish-trigger'] = schedulers.Triggerable(
        name="publish-trigger",
        builderNames=[prefix+'_builder'],
    )
    cfg['schedulers']['publish-ara-force'] = schedulers.ForceScheduler(
        name="publish-ara-force",
        builderNames=[prefix+'_ara_builder'],
        properties=[
            util.StringParameter(name="path",
                                 label="Path:",
                                 default="", size=80),
        ],
    )
    cfg['schedulers']['publish-ara-trigger'] = schedulers.Triggerable(
        name="publish-ara-trigger",
        builderNames=[prefix+'_ara_builder'],
    )

    # update the whitelist every day at 3am
    cfg['schedulers'][prefix+'-whitelist'] = schedulers.Nightly(
        name="whitelist",
        builderNames=[prefix+'_whitelist'],
        hour=3, minute=0,
    )

    # update the user cvmfs space every hour on the hour
    cfg['schedulers'][prefix+'-user_rsync'] = schedulers.Nightly(
        name="user cvmfs",
        builderNames=[prefix+'_user_rsync'],
        minute=0,
    )

    # backup cvmfs the first day of every month, at 4am
    cfg['schedulers'][prefix+'-backup'] = schedulers.Nightly(
        name="backup",
        builderNames=[prefix+'_backup'],
        dayOfMonth=1, hour=4, minute=0,
    )


config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
config.locks['cvmfs_publish'] = util.MasterLock('cvmfs_publish', maxCount=1)
