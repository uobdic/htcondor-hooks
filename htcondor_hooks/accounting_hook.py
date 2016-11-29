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


def get_local_user(job_ad):
    user_plus_domain = str(job_ad['User'])
    user = user_plus_domain.split('@')[0]
    LOG.debug('Identified submitter as {0}'.format(user))
    return user


def get_job_ad():
    import classad
    try:
        line = sys.stdin.readline()
        route_ad = classad.ClassAd(line)
    except SyntaxError:
        LOG.error("Unable to parse classad: {0}".format(line))
        return None

    separator_line = sys.stdin.readline()
    try:
        assert separator_line == "------\n"
    except AssertionError:
        LOG.error("Separator line was not second line of STDIN")
        return None

    try:
        job_ad = classad.parseOne(sys.stdin, parser=classad.Parser.New)
    except SyntaxError:
        LOG.error("Unable to parse classad")
        return None

    return job_ad


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


def setup_LOG(config):
    log_level = getattr(logging, config['hook']['log_level'])
    LOG.setLevel(log_level)
    logFormatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

    fileHandler = logging.FileHandler(config['hook']['log_file'])
    fileHandler.setFormatter(logFormatter)
    LOG.addHandler(fileHandler)


if __name__ == '__main__':
    config = get_config(CONFIG_FILE)
    setup_LOG(config)

    job_ad = get_job_ad()
    job_id = '{0}.{1}'.format(job_ad['ClusterId'], job_ad['ProcId'])
    LOG.debug("processing job {0}".format(job_id))

    user = get_local_user(job_ad)
    group = get_accounting_group_for_user(config, user)
    job_ad = set_accounting(job_ad, group, user)

    print(job_ad.printOld())
    sys.exit(SUCCESS)
