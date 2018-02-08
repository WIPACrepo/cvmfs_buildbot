# iceprod_buildbot/worker-cvmfs-centos6-build

FROM centos:6

LABEL description="IceCube - CVMFS buildbot worker with devel packages running centos:6" \
      mounts="cvmfs" \
      cpus="4" \
      memory="8000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos6-build" \
      version="0.1.11"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc gcc-c++ gcc-gfortran autoconf automake make \
        m4 bison flex expat-devel centos-release-scl \
        libtool patch binutils unzip git subversion wget curl \
        libpng-devel openssl-devel libX11-devel bzip2-devel \
        ncurses-devel readline-devel libXext-devel libXi-devel \
        libXfixes-devel libXft-devel libXmu-devel libXpm-devel \
        libXrandr-devel libXt-devel freeglut-devel libffi-devel \
        file which && \
    yum -y install python27 devtoolset-3-gcc devtoolset-3-gcc-c++ \
        devtoolset-3-gcc-gfortran && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init && \
    scl enable python27 'curl "https://bootstrap.pypa.io/get-pip.py" | python' && \
    scl enable python27 "pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker" && \
    mkdir /cvmfs && mkdir -p /usr/share/buildbot && \
    echo -e "#!/bin/sh\nscl enable devtoolset-3 python27 'twistd -ny buildbot.tac'" > /usr/share/buildbot/run.sh && \
    chmod +x /usr/share/buildbot/run.sh && \
    useradd -m -u 1000 -s /bin/bash buildbot && chown -R buildbot /buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash","-c","chown buildbot /cvmfs; su -c /usr/share/buildbot/run.sh buildbot"]
