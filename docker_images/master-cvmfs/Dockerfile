# icecube-buildbot/master-cvmfs

FROM centos:7

LABEL description="IceCube - CVMFS buildbot master running centos:7" \
      mounts="data" \
      cpus="1" \
      memory="1000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="master-cvmfs" \
      version="0.1.1"

RUN \
    yum clean all && \
    yum -y install gcc make unzip git subversion wget curl \
        patch binutils file which libffi python-devel && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init buildbot[bundle,tls] && \
    mkdir /buildbot && mkdir /data && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot /data

USER buildbot

WORKDIR /data

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash","-c","export PYTHONPATH=/buildbot;if [ ! -e 'buildbot.tac' ]; then buildbot create-master . ; fi; rm -f master.cfg twistd.pid; ln -s /buildbot/master.cfg master.cfg; twistd -l - -ny buildbot.tac"]
