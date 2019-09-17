#!/bin/env python
'''
Reads a configuration file of the form
[blacklist]
sm23.hadoop.cluster

and applies the blacklist classads to all routed jobs.
'''
import os
import json
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
htcondor_hooks_path = os.path.join(dir_path, '..')
sys.path.insert(0, htcondor_hooks_path)

from htcondor_hooks.core import get_job_ad

SUCCESS = 0
FAILURE = 1


CONFIG_FILE = "/etc/default/htcondor-blacklist.json"


def get_config(config_file):
    if not os.path.exists(config_file):
        raise IOError("Could not find {0}".format(config_file))
    config = {}
    with open(config_file) as f:
        config = json.load(f)

    return config


def construct_blacklist(job_ad, config):
    import classad
    blacklist = config['blacklist']
    if not blacklist:
        return job_ad

    template = '( machine != "{machine}" )'
    blacklist_machines = []
    for machine in blacklist:
        blacklist_machines.append(template.format(machine=machine))

    blacklist_machines = ' && '.join(blacklist_machines)

    requirements = job_ad['Requirements']
    requirements = classad.Literal(str(requirements) + ' && ' + blacklist_machines)

    job_ad['Requirements'] = requirements


    return job_ad


if __name__ == '__main__':
    config = get_config(CONFIG_FILE)
    job_ad = get_job_ad()
    if job_ad is None:
        sys.exit(FAILURE)
    job_id = '{0}.{1}'.format(job_ad['ClusterId'], job_ad['ProcId'])

    job_ad = construct_blacklist(job_ad, config)

    print(job_ad.printOld())
    sys.exit(SUCCESS)
