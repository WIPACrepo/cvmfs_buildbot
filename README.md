# cvmfs_buildbot
Buildbot for cvmfs software.

* regular software releases `pyX-vY`
* iceprod releases `iceprod/XXX`
* user space `users/XXX`

## Changing the config
When changing config in `master_cfg_d`, this is the update process:

1. `python setup_kubernetes.py`
2. `kubectl replace -f kubernetes/buildbot-master-cfg-d.json`
3. `kubectl delete pod cvmfs-buildbot-XXXX-YYY`


