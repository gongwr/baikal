# Copyright (c) 2023 WenRui Gong
# All Rights Reserved.

"""
Baikal API Server
"""

import os
import sys

from oslo_reports import guru_meditation_report as gmr
from oslo_utils import encodeutils

# If ../baikal/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir,
                                                os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'baikal', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from oslo_config import cfg
from oslo_log import log as logging
import osprofiler.initializer

from baikal.common import config
from baikal.common import exception
from baikal import version

CONF = cfg.CONF
logging.register_options(CONF)

# NOTE(rosmaita): Any new exceptions added should preserve the current
# error codes for backward compatibility.  The value 99 is returned
# for errors not listed in this map.
ERROR_CODE_MAP = {RuntimeError: 1,
                  exception.WorkerCreationFailure: 2,
                  ValueError: 3,
                  cfg.ConfigFileValueError: 4}


def fail(e):
    sys.stderr.write("ERROR: %s\n" % encodeutils.exception_to_unicode(e))
    return_code = ERROR_CODE_MAP.get(type(e), 99)
    sys.exit(return_code)


def main():
    try:
        config.parse_args()
        config.set_config_defaults()
        logging.setup(CONF, "baikal")
        gmr.TextGuruMeditation.setup_autorun(version)

        if CONF.profiler.enabled:
            osprofiler.initializer.init_from_conf(
                conf=CONF,
                context={},
                project="baikal",
                service="api",
                host=CONF.bind_host
            )

        LOG = logging.getLogger(__name__)
        LOG.info('Starting Baikal API Server version %s' % version.version_string())

        server = config.get_server()
        server.start()
        server.wait()
    except Exception as e:
        fail(e)


if __name__ == '__main__':
    main()
