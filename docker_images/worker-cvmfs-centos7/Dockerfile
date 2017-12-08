# iceprod_buildbot/worker-cvmfs-centos7

FROM centos:7

LABEL description="IceCube - CVMFS buildbot worker running centos:7" \
      mounts="cvmfs" \
      cpus="1" \
      memory="1000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos7" \
      version="0.1"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc make unzip git subversion wget curl \
        patch binutils file which libffi python-devel \
        gawk fuse fuse-libs attr policycoreutils-python && \
    yum clean all && \
    mkdir /cvmfs && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot

USER buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash", "-c", "twistd -ny buildbot.tac"]
