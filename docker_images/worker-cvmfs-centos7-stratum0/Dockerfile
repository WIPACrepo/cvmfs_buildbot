# iceprod_buildbot/worker-cvmfs-centos7-stratum0

FROM centos:7

LABEL description="IceCube - CVMFS buildbot worker running centos:7" \
      mounts="cvmfs" \
      cpus="1" \
      memory="6000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-cvmfs-centos7-stratum0" \
      version="0.1.27"

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
    printf "#!/bin/sh\ntwistd -ny buildbot.tac" > /buildbot/start.sh && \
    chmod +x /buildbot/start.sh && \
    printf "#!/bin/sh\nfor e in \$(tr '\\\\000' '\\\\n' < /proc/1/environ); do\neval \"export \$e\"\ndone\nsleep 30\nrunuser buildbot /buildbot/start.sh" > /buildbot/setupenv.sh && \
    chmod +x /buildbot/setupenv.sh && \
    useradd -m -u 1000 -s /bin/bash buildbot && chown -R buildbot /buildbot && \
    mkdir -p /mnt/cvmfs_config && \
    (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done) && \
    rm -f /lib/systemd/system/multi-user.target.wants/* && \
    rm -f /etc/systemd/system/*.wants/* && \
    rm -f /lib/systemd/system/local-fs.target.wants/* && \
    rm -f /lib/systemd/system/sockets.target.wants/*udev* && \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl* && \
    rm -f /lib/systemd/system/basic.target.wants/* && \
    rm -f /lib/systemd/system/anaconda.target.wants/* && \
    printf "[Unit]\nDescription=CVMFS-setup\nAfter=httpd.target\n\n[Service]\nUser=root\nGroup=root\nWorkingDirectory=/\nExecStart=/buildbot/stratum0-start.sh\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/cvmfs-setup.service && \
    printf "[Unit]\nDescription=Buildbot\nAfter=cvmfs-setup.target\n\n[Service]\nUser=root\nGroup=root\nWorkingDirectory=/buildbot\nExecStart=/buildbot/setupenv.sh\n\n[Install]\nWantedBy=multi-user.target" > /etc/systemd/system/buildbot.service && \
    systemctl enable httpd && \
    systemctl enable cvmfs-setup && \
    systemctl enable buildbot && \
    echo 'root' | passwd root --stdin

STOPSIGNAL SIGRTMIN+3

CMD ["bash","-c","/sbin/init"]
