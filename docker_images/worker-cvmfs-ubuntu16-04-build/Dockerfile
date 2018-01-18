# iceprod_buildbot/worker-cvmfs-ubuntu16-04-build

FROM ubuntu:16.04

LABEL description="IceCube - CVMFS buildbot worker with devel packages running ubuntu:16.04" \
      mounts="cvmfs" \
      cpus="4" \
      memory="8000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-ubuntu16-04-build" \
      version="0.1.6"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    apt-get update && \
    apt-get -y install build-essential autoconf automake make \
        m4 bison flex gfortran pkg-config \
        libtool patch binutils unzip git subversion wget curl \
        libpng-dev libssl-dev libx11-dev zlib1g-dev libbz2-dev \
        libncurses5-dev libreadline-dev freeglut3-dev libffi-dev \
        file python-dev && \
    apt-get -y clean && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    mkdir /cvmfs && mkdir -p /usr/share/buildbot && \
    printf "#!/bin/sh\ntwistd -ny buildbot.tac" > /usr/share/buildbot/run.sh && \
    chmod +x /usr/share/buildbot/run.sh && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]

CMD ["bash","-c","chown -R buildbot /cvmfs; runuser buildbot /usr/share/buildbot/run.sh"]
