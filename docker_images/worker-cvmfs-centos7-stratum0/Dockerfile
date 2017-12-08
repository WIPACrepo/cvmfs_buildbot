# iceprod_buildbot/worker-cvmfs-centos7-stratum0

FROM centos:7

LABEL description="IceCube - CVMFS buildbot worker running centos:7" \
      mounts="cvmfs" \
      cpus="1" \
      memory="1000" \
      gpus="0" \
      disk="50" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos7-stratum0" \
      version="0.1.6"

COPY buildbot.tac /buildbot/buildbot.tac
COPY stratum0-start.sh /buildbot/stratum0-start.sh

ENV container docker

RUN \
    yum clean all && \
    yum -y install epel-release gcc make unzip git subversion wget curl \
        patch binutils file which libffi python-devel \
        gawk fuse fuse-libs attr policycoreutils-python && \
    yum -y install https://ecsft.cern.ch/dist/cvmfs/cvmfs-release/cvmfs-release-latest.noarch.rpm && \
    yum -y install cvmfs cvmfs-server && \
    yum clean all && \
    mkdir /cvmfs-source && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    chmod +x /buildbot/stratum0-start.sh && \
    echo -e "#!/bin/sh\ntwistd -ny buildbot.tac" > /buildbot/start.sh && chmod +x /buildbot/start.sh && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot && \
    mkdir -p /mnt/cvmfs_config && \
    echo -e "[Unit]\nDescription=CVMFS-setup\nAfter=httpd.target\n\n[Service]\nUser=root\nGroup=root\nWorkingDirectory=/\nExecStart=/buildbot/stratum0-start.sh\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/cvmfs-setup.service && \
    echo -e "[Unit]\nDescription=Buildbot\nAfter=cvmfs-setup.target\n\n[Service]\nUser=buildbot\nGroup=buildbot\nWorkingDirectory=/buildbot\nExecStart=/buildbot/start.sh\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/buildbot.service && \
    systemctl enable httpd && \
    systemctl enable cvmfs-setup && \
    systemctl enable buildbot && \
    echo 'root' | passwd root --stdin

STOPSIGNAL SIGRTMIN+3

CMD ["/sbin/init"]
