from __future__ import print_function

import os
import platform

from buildbot.plugins import *


def get_os():
    d = platform.linux_distribution()
    os = d[0].lower()
    if os not in ('ubuntu','debian','centos'):
        if 'red hat' in os:
            os = 'centos'
        else:
            raise Exception('unknown os: '+os)
    ver = d[1].lower().split('/')[-1]
    if os == 'centos':
        ver = ver.split('.')[0]
    try:
        float(ver)
    except:
        return os+'_'+ver
    else:
        return os+ver


class WriteOnceDict(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError('{} has already been set'.format(key))
        super(WriteOnceDict, self).__setitem__(key, value)

class Config(dict):
    """
    A Config object, holding the setup for a BuildBot config.

    Provide a setup function
    """
    def __init__(self, setup=None):
        self['change_source'] = WriteOnceDict()
        self['workers'] = WriteOnceDict()
        self['builders'] = WriteOnceDict()
        self['schedulers'] = WriteOnceDict()

        self.locks = WriteOnceDict()
        self.codebases = WriteOnceDict()

        self.dependencies = []
        self.setup = setup

    def register_dependency(self, dep):
        self.dependencies.append(dep)

    def __call__(self):
        name = self.setup.__module__.split('.')[-1] if self.setup else 'None'
        print(name,'pre-dep locks:',self.locks)
        for d in self.dependencies:
            d.locks.update(self.locks)
            d()
            self.codebases.update(d.codebases)
            for k in self:
                self[k].update(d[k])
        dep_sched = [self['schedulers'][s].name for s in self['schedulers'] if self['schedulers'][s].__class__.__name__ == 'Triggerable']
        dep_builders = set(self['builders'])

        if self.setup:
            print(name,'pre-setup locks:',self.locks)
            self.setup(self)

        # for any new factory made by setup, add dependency trigger
        if dep_sched:
            for b in self['builders']:
                if b not in dep_builders:
                    self['builders'][b].factory.addStep(steps.Trigger(
                        schedulerNames=dep_sched,
                        waitForFinish=False,
                        updateSourceStamp=False,
                    ))
