from __future__ import absolute_import

import logging

from .mockinterface.mocknode import PyrosMock
from .pyros_client import PyrosClient

from collections import namedtuple
from contextlib import contextmanager


# A context manager to handle server process launch and shutdown properly.
# It also creates a communication channel and passes it to a client.
@contextmanager
# TODO : think about passing ros arguments http://wiki.ros.org/Remapping%20Arguments
def pyros_ctx(name='pyros', argv=None, anonymous=True, disable_signals=True, mock=False, base_path=None):

    if mock:
        subproc = PyrosMock(name)
    else:
        # dynamic import
        try:
            # this will import rosinterface and if needed simulate ROS setup
            import sys
            from . import rosinterface
            sys.modules[".rosinterface"] = rosinterface.delayed_import_auto(distro='indigo', base_path=base_path)
            from .rosinterface.pyros_ros import PyrosROS
        except ImportError, e:
            import logging
            logging.warn("Error: Could not import PyrosROS from .rosinterface.pyros_ros {}".format(e))

            # TODO : maybe turn this whole setup behavior into a context so we can cleanup easily

        subproc = PyrosROS(name, argv, base_path=base_path)

    client_conn = subproc.start()

    ctx = namedtuple("pyros_context", "client")
    yield ctx(client=PyrosClient(client_conn))

    subproc.shutdown()
