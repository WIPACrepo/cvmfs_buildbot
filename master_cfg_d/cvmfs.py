from __future__ import print_function

import os
import json
import random

from buildbot.plugins import *
from buildbot.process.buildstep import SUCCESS,SKIPPED

from . import Config, get_os


prefix = __file__.split('/')[-1].rsplit('.',1)[0]

worker_cfgs = {
    'cvmfs-centos6-build': 'worker-cvmfs-centos6-build',
    'cvmfs-centos7-build': 'worker-cvmfs-centos7-build',
    'cvmfs-ubuntu14-04-build': 'worker-cvmfs-ubuntu14-04-build',
    'cvmfs-ubuntu15-10-build': 'worker-cvmfs-ubuntu15-10-build',
    'cvmfs-ubuntu16-04-build': 'worker-cvmfs-ubuntu16-04-build',
    'cvmfs-ubuntu18-04-build': 'worker-cvmfs-ubuntu18-04-build',
}

def setup(cfg):

    ####### WORKERS

    for name in worker_cfgs:
        cfg['workers'][name] = worker.Worker(
            name, os.environ['WORKER_PASSWORD'],
            max_builds=2,
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
    
    @util.renderer
    def makeCommand(props):
        command = [
            'python', 'builders/build.py',
            '--src', 'icecube.opensciencegrid.org',
            '--dest', '/cvmfs/icecube.opensciencegrid.org',
            '--variant', props.getProperty('variant'),
        ]
        if props.getProperty('svnonly'):
            command.extend([
                '--svnup', 'True',
                '--svnonly', 'True',
            ])
        else:
            command.extend([
                '--svnup', 'False',
            ])
        if props.getProperty('nightly'):
            command.append(['--nightly'])
        return command
    
    @util.renderer
    def makeCommandSpack(props):
        command = [
            'python', 'spack/build.py',
            '--src', 'icecube.opensciencegrid.org',
            '--dest', '/cvmfs/icecube.opensciencegrid.org',
            props.getProperty('variant'),
        ]
        return command

    build_factory = util.BuildFactory()
    build_factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    build_factory.addStep(steps.ShellCommand(
        name='build cvmfs',
        command=makeCommand,
        env={
            'CPUS': util.Property('CPUS', default='1'),
#            'MEMORY': util.Property('MEMORY', default='1'),
        },
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))
    

    build_factory_spack = util.BuildFactory()
    build_factory_spack.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    build_factory_spack.addStep(steps.ShellCommand(
        name='build cvmfs',
        command=makeCommandSpack,
        env={
            'CPUS': util.Property('CPUS', default='1'),
#            'MEMORY': util.Property('MEMORY', default='1'),
        },
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('counting')
        ],
    ))

    @util.renderer
    def isMetaproject(props):
        return 'meta' in props.getProperty('variant',default='')

    svn_factory = util.BuildFactory()
    svn_factory.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    svn_factory.addStep(steps.ShellCommand(
        name='svn checkout',
        command=makeCommand,
        env={
            'CPUS': util.Property('CPUS', default='1'),
#            'MEMORY': util.Property('MEMORY', default='1'),
        },
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive')
        ],
        doStepIf=isMetaproject,
    ))
    svn_factory.addStep(steps.Trigger(schedulerNames=[prefix+'-build'],
        waitForFinish=True,
        updateSourceStamp=True,
        haltOnFailure=True,
        set_properties={
            'variant': util.Property('variant'),
            'nightly': util.Property('nightly'),
            'svnonly': False,
        }
    ))
    @util.renderer
    def translate_variant_to_path(props):
        variant = str(props.getProperty('variant')).split('_')[:-1]
        if len(variant) < 2:
            return variant[0]
        return variant[0]+'-'+'.'.join(variant[1:])
    svn_factory.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': translate_variant_to_path,
        }
    ))
    
    spack_master = util.BuildFactory()
    spack_master.addStep(steps.Git(
        repourl='git://github.com/WIPACrepo/cvmfs.git',
        mode='full',
        method='clobber',
        workdir='build',
    ))
    spack_master.addStep(steps.ShellCommand(
        name='svn checkout',
        command=makeCommandSpack,
        env={
            'CPUS': util.Property('CPUS', default='1'),
#            'MEMORY': util.Property('MEMORY', default='1'),
        },
        workdir='build',
        haltOnFailure=True,
        locks=[
            cfg.locks['cvmfs_shared'].access('exclusive')
        ],
        doStepIf=isMetaproject,
        timeout=3600*4, # 4 hours - some packages take a long time to build
    ))
    spack_master.addStep(steps.Trigger(schedulerNames=[prefix+'-build-spack'],
        waitForFinish=True,
        updateSourceStamp=True,
        haltOnFailure=True,
        set_properties={
            'variant': util.Property('variant'),
            'nightly': util.Property('nightly'),
            'svnonly': False,
        }
    ))
    @util.renderer
    def translate_variant_to_path_spack(props):
        variant = str(props.getProperty('variant')).replace('-meta','')
        return variant
    spack_master.addStep(steps.Trigger(schedulerNames=['publish-trigger'],
        waitForFinish=True,
        set_properties={
            'variant': translate_variant_to_path_spack,
        }
    ))

    builders = []
    for name in worker_cfgs:
        cfg['builders'][name+'_builder'] = util.BuilderConfig(
            name=name+'_builder',
            workername=name,
            factory=build_factory,
            properties={},
        )
        builders.append(name+'_builder')

    builders_spack = []
    for name in worker_cfgs:
        if 'ubuntu14' in name:
            continue
        cfg['builders'][name+'_builder_spack'] = util.BuilderConfig(
            name=name+'_builder_spack',
            workername=name,
            factory=build_factory_spack,
            properties={},
        )
        builders_spack.append(name+'_builder_spack')

    cfg['builders']['svn_builder'] = util.BuilderConfig(
        name='svn_builder',
        workername='cvmfs-ubuntu18-04-build',
        factory=svn_factory,
        properties={},
    )

    cfg['builders']['svn_builder_spack'] = util.BuilderConfig(
        name='svn_builder_spack',
        workername='cvmfs-ubuntu18-04-build',
        factory=spack_master,
        properties={},
    )

    ####### SCHEDULERS

    variants = ['py2_v3.0.1_base','py2_v3.0.1_metaproject','iceprod']
    for v in variants:
        cfg['schedulers'][prefix+'-'+v] = schedulers.SingleBranchScheduler(
            name=prefix+'-'+v,
            change_filter=util.ChangeFilter(category=prefix),
            treeStableTimer=None,
            builderNames=['svn_builder'],
            properties={'variant':v, 'svnonly':True, 'nightly':False},
        )
    cfg['schedulers'][prefix+'-triggerable'] = schedulers.Triggerable(
        name=prefix+"-build",
        builderNames=builders,
    )
    cfg['schedulers'][prefix+'-triggerable-spack'] = schedulers.Triggerable(
        name=prefix+"-build-spack",
        builderNames=builders_spack,
    )
    cfg['schedulers'][prefix+'-force'] = schedulers.ForceScheduler(
        name=prefix+"-force",
        builderNames=['svn_builder'],
        properties=[
            util.StringParameter(name="variant",
                                 label="Variant:",
                                 default="", size=80),
            util.BooleanParameter(name="nightly",
                                  label="Nightly build",
                                  default=False),
            util.FixedParameter(name="svnonly", default="True"),
        ],
    )
    cfg['schedulers'][prefix+'-force-spack'] = schedulers.ForceScheduler(
        name=prefix+"-force-spack",
        builderNames=['svn_builder_spack'],
        properties=[
            util.StringParameter(name="variant",
                                 label="Variant:",
                                 default="", size=80),
            util.BooleanParameter(name="nightly",
                                  label="Nightly build",
                                  default=False),
            util.FixedParameter(name="svnonly", default="True"),
        ],
    )

    cfg['schedulers'][prefix+'-nightly'] = schedulers.Nightly(
        name=prefix+'-nightly',
        builderNames=['svn_builder'],
        properties={'variant':'py2_v3_1_1_metaproject', 'svnonly': True, 'nightly':True},
        hour=0, minute=0,
    )

config = Config(setup)
config.locks['cvmfs_shared'] = util.MasterLock('cvmfs_lock', maxCount=100)
