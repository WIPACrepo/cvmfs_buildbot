# iceprod_buildbot/worker-cvmfs-centos7-build

FROM centos:7

LABEL description="IceCube - CVMFS buildbot worker with devel packages running centos:7" \
      mounts="cvmfs" \
      cpus="4" \
      memory="8000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos7-build" \
      version="0.1.6"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc gcc-c++ gcc-gfortran autoconf automake make \
        m4 bison flex \
        libtool patch binutils unzip git subversion wget curl \
        libpng-devel openssl-devel libX11-devel bzip2-devel \
        ncurses-devel readline-devel libXext-devel libXi-devel \
        libXfixes-devel libXft-devel libXmu-devel libXpm-devel \
        libXrandr-devel libXt-devel freeglut-devel libffi-devel \
        file which python-devel && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    mkdir /cvmfs && mkdir -p /usr/share/buildbot && \
    echo -e "#!/bin/sh\ntwistd -ny buildbot.tac" > /usr/share/buildbot/run.sh && \
    chmod +x /usr/share/buildbot/run.sh && \
    useradd -m -u 1000 -s /bin/bash buildbot && chown -R buildbot /buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash","-c","chown buildbot /cvmfs; runuser buildbot /usr/share/buildbot/run.sh"]
