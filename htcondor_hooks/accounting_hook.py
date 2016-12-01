#!/bin/env python
'''
Reads a configuration file of the form
[hook]
ignore_routes = 
log_file=/tmp/accounting-translate-hook.log
log_level=INFO

[groups]
physics.hep = \
user1,user2,\
user5,user7

physics.hep.susy = user3,user4

default_group = physics.hep


and applies the accounting_group and accounting_group_user classads to all routed jobs.
'''
import logging
import os
import ConfigParser
import sys
from .core import get_job_ad, setup_logger, get_local_user
SUCCESS = 0
FAILURE = 1

LOG = logging.getLogger("htcondor-accounting-job-router")

CONFIG_FILE = "/etc/default/htcondor-accounting-job-router.ini"


def get_config(config_file):
    if not os.path.exists(config_file):
        raise IOError("Could not find {0}".format(config_file))
    config = {}
    config['groups'] = {}
    config['hook'] = {}
    conf = ConfigParser.ConfigParser()
    conf.read(config_file)

    for option in conf.options('hook'):
        config['hook'][option] = conf.get('hook', option)

    groups = conf.options('groups')
    for group in groups:
        if not group == 'default_group':
            config['groups'][group] = conf.get('groups', group).split(',')
        else:
            config['groups'][group] = conf.get('groups', group)
    LOG.info(config)
    return config


def get_user_mapping(config):
    """
    Invert the definition in the config (group -> user) so can ask which group
    a user belongs to
    """
    user_map = {}

    for group, users in config['groups'].items():
        if group == 'default_group':
            continue
        for user in users:
            if user in user_map:
                msg = "User {0} already exists for group {1}".format(
                    user,
                    user_map[user],
                )
                raise ValueError(msg)
            user_map[user] = group

    return user_map


def get_accounting_group_for_user(config, user):
    user_map = get_user_mapping(config)
    default_group = config['groups']['default_group']

    if user in user_map:
        return user_map[user]
    else:
        msg = "Did not find explicit mapping for user {0}, using default group '{1}'"
        msg = msg.format(user, default_group)
        LOG.warn(msg)
        return default_group


def set_accounting(job_ad, group, user):
    # translate to condor group
    LOG.debug('Setting accounting group as {0}'.format(group))

    group = 'group_' + group + '.' + user

    job_ad['AcctGroupUser'] = user
    job_ad['AccountingGroup'] = group
    
    return job_ad


if __name__ == '__main__':
    config = get_config(CONFIG_FILE)
    setup_logger(config, LOG)
    
    job_ad = get_job_ad(LOG)
    if job_ad is None:
        sys.exit(FAILURE)
#    print(job_ad)
    job_id = '{0}.{1}'.format(job_ad['ClusterId'], job_ad['ProcId'])
    LOG.debug("processing job {0}".format(job_id))

    user = get_local_user(job_ad, LOG)
    group = get_accounting_group_for_user(config, user)
    job_ad = set_accounting(job_ad, group, user)

    print(job_ad.printOld())
    sys.exit(SUCCESS)
