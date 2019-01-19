# iceprod_buildbot/worker-cvmfs-centos6-build

FROM centos:6

LABEL description="IceCube - CVMFS buildbot worker with devel packages running centos:6" \
      mounts="cvmfs" \
      cpus="4" \
      memory="8000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos6-build" \
      version="0.1.17"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    printf '[slc6-devtoolset]\nname=Scientific Linux CERN 6 (SLC6) - Devtoolset addons\nbaseurl=http://linuxsoft.cern.ch/cern/devtoolset/slc6X/$basearch/yum/devtoolset/\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-cern\ngpgcheck=0\nenabled=1\nprotect=1' > /etc/yum.repos.d/slc6-devtoolset.repo && \
    yum clean all && \
    yum -y install gcc gcc-c++ gcc-gfortran autoconf automake make \
        m4 bison flex expat-devel centos-release-scl \
        libtool patch binutils unzip git subversion wget curl \
        libpng-devel openssl-devel libX11-devel bzip2-devel \
        ncurses-devel readline-devel libXext-devel libXi-devel \
        libXfixes-devel libXft-devel libXmu-devel libXpm-devel \
        libXrandr-devel libXt-devel freeglut-devel libffi-devel \
        file which xz libxml2-devel && \
    yum -y install python27 devtoolset-2-gcc devtoolset-2-gcc-c++ \
        devtoolset-2-gcc-gfortran devtoolset-2-binutils && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/2.6/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init && \
    scl enable python27 'curl "https://bootstrap.pypa.io/get-pip.py" | python' && \
    scl enable python27 "pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker" && \
    mkdir /cvmfs && mkdir -p /usr/share/buildbot && \
    echo -e "#!/bin/sh\nscl enable devtoolset-2 python27 'twistd -ny buildbot.tac'" > /usr/share/buildbot/run.sh && \
    chmod +x /usr/share/buildbot/run.sh && \
    useradd -m -u 1000 -s /bin/bash buildbot && chown -R buildbot /buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash","-c","chown buildbot /cvmfs; su -c /usr/share/buildbot/run.sh buildbot"]
