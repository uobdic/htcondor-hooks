import sys
import logging


def get_job_ad(logger):
    import classad
    instream = sys.stdin
    route = ""
    while True:
        newline = instream.readline()
        if newline.startswith("------"):
            break
        route += newline

    try:
        job_ad = classad.parseOne(instream, parser=classad.Parser.Old)
    except (SyntaxError, ValueError):
        logger.error(
            "Unable to parse classad: {0}".format(instream.readlines()))
        return None

    return job_ad


def setup_logger(config, logger):
    log_level = getattr(logging, config['hook']['log_level'])
    logger.setLevel(log_level)
    logFormatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

    fileHandler = logging.FileHandler(config['hook']['log_file'])
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)


def get_local_user(job_ad, logger):
    user_plus_domain = str(job_ad['User'])
    user = user_plus_domain.split('@')[0]
    logger.debug('Identified submitter as {0}'.format(user))
    return user
