# icecube-buildbot/master-cvmfs

FROM centos:7

LABEL description="IceCube - CVMFS buildbot master running centos:7" \
      mounts="buildbot,data" \
      cpus="1" \
      memory="1000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="master-cvmfs" \
      version="0.1.17"

COPY buildbot.tac /usr/share/buildbot/buildbot.tac
COPY run.sh /usr/share/buildbot/run.sh

RUN \
    yum clean all && \
    yum -y install gcc make unzip git subversion wget curl \
        patch binutils file which libffi python-devel && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init buildbot[bundle,tls] && \
    mkdir /buildbot && mkdir /data && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot /data /usr/share/buildbot

WORKDIR /data

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash","-c","chown -R buildbot /buildbot /data; runuser buildbot /usr/share/buildbot/run.sh"]
