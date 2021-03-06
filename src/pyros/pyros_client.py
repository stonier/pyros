from __future__ import absolute_import

import logging
import unicodedata

import sys

"""
Client to rostful node, Python style.
Required for multiprocess communication.
"""

import zmp
from .exceptions import PyrosException

# TODO : Requirement : Check TOTAL send/receive SYMMETRY.
# If needed get rid of **kwargs arguments in call. Makes the interface less obvious and can trap unaware devs.


class PyrosServiceNotFound(PyrosException):
    def __init__(self, message):
        super(PyrosServiceNotFound, self).__init__(message)
        self.excmsg = message

    @property
    def message(self):
        return self.excmsg


# CAREFUL : exceptions must be pickleable ( we need to pass all arguments to the superclass )
class PyrosServiceTimeout(PyrosException):
    def __init__(self, message):
        super(PyrosServiceTimeout, self).__init__(message)
        self.excmsg = message

    @property
    def message(self):
        return self.excmsg

PyrosException.register(PyrosServiceTimeout)


class PyrosClient(object):
    def __init__(self, node_name=None):
        # Link to only one Server
        self.node_name = node_name

        # Discover all Services. Wait for at least one, and make sure it s provided by our expected Server
        self.msg_build_svc = zmp.Service.discover('msg_build', 5)
        if self.msg_build_svc is None or (
            self.node_name is not None and
            self.node_name not in self.msg_build_svc.providers
        ):
            raise PyrosServiceNotFound('msg_build')

        self.topic_svc = zmp.Service.discover('topic', 5)
        if self.topic_svc is None or (
            self.node_name is not None and
            self.node_name not in self.topic_svc.providers
        ):
            raise PyrosServiceNotFound('topic')

        self.service_svc = zmp.Service.discover('service', node_name, 5)
        if self.service_svc is None or (
            self.node_name is not None and
            self.node_name not in self.service_svc.providers
        ):
            raise PyrosServiceNotFound('service')

        self.param_svc = zmp.Service.discover('param', node_name, 5)
        if self.param_svc is None or (
            self.node_name is not None and
            self.node_name not in self.param_svc.providers
        ):
            raise PyrosServiceNotFound('param')

        self.topics_svc = zmp.Service.discover('topics', 5)
        if self.topics_svc is None or (
            self.node_name is not None and
            self.node_name not in self.topics_svc.providers
        ):
            raise PyrosServiceNotFound('topics')

        self.services_svc = zmp.Service.discover('services', 5)
        if self.services_svc is None or (
            self.node_name is not None and
            self.node_name not in self.services_svc.providers
        ):
            raise PyrosServiceNotFound('services')

        self.params_svc = zmp.Service.discover('params', 5)
        if self.params_svc is None or (
            self.node_name is not None and
            self.node_name not in self.params_svc.providers
        ):
            raise PyrosServiceNotFound('params')

        # ROCON stuff
        # self.namespaces_svc = zmp.Service.discover('namespaces', 5)
        # if self.namespaces_svc is None or (
        #     self.node_name is not None and
        #     self.node_name not in self.namespaces_svc.providers
        # ):
        #     raise PyrosServiceNotFound('namespaces')

        # self.interactions_svc = zmp.Service.discover('interactions', 5)
        # if self.interactions_svc is None or (
        #     self.node_name is not None and
        #     self.node_name not in self.interactions_svc.providers
        # ):
        #     raise PyrosServiceNotFound('interactions')

        # self.interaction_svc = zmp.Service.discover('interaction', 5)
        # if self.interaction_svc is None or (
        #     self.node_name is not None and
        #     self.node_name not in self.interaction_svc.providers
        # ):
        #     raise PyrosServiceNotFound('interaction')

        # self.has_rocon_svc = zmp.Service.discover('has_rocon', 5)
        # if self.has_rocon_svc is None or (
        #     self.node_name is not None and
        #     self.node_name not in self.has_rocon_svc.providers
        # ):
        #     raise PyrosServiceNotFound('has_rocon')



    def buildMsg(self, connection_name, suffix=None):
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(connection_name, unicode):
            connection_name = unicodedata.normalize('NFKD', connection_name).encode('ascii', 'ignore')
        res = self.msg_build_svc.call(args=(connection_name,))
        return res

    def topic_inject(self, topic_name, _msg_content=None, **kwargs):
        """
        Injecting message into topic. if _msg_content, we inject it directly. if not, we use all extra kwargs
        :param topic_name: name of the topic
        :param _msg_content: optional message content
        :param kwargs: each extra kwarg will be put int he message is structure matches
        :return:
        """
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(topic_name, unicode):
            topic_name = unicodedata.normalize('NFKD', topic_name).encode('ascii', 'ignore')

        if _msg_content is not None:
            res = self.topic_svc.call(args=(topic_name, _msg_content,))
        else:  # default kwargs is {}
            res = self.topic_svc.call(args=(topic_name, kwargs,))

        return res is None  # check if message has been consumed

    def topic_extract(self, topic_name):
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(topic_name, unicode):
            topic_name = unicodedata.normalize('NFKD', topic_name).encode('ascii', 'ignore')

        res = self.topic_svc.call(args=(topic_name, None,))

        return res

    def service_call(self, service_name, _msg_content=None, **kwargs):
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(service_name, unicode):
            service_name = unicodedata.normalize('NFKD', service_name).encode('ascii', 'ignore')

        try:
            if _msg_content is not None:
                res = self.service_svc.call(args=(service_name, _msg_content,))
            else:  # default kwargs is {}
                res = self.service_svc.call(args=(service_name, kwargs,))
        except zmp.service.ServiceCallTimeout, exc:
            raise PyrosServiceTimeout("Pyros Service call timed out."), None, sys.exc_info()[2]
        # A service that doesn't exist on the node will return res_content.resp_content None.
        # It should probably except...
        # TODO : improve error handling, maybe by checking the type of res ?

        return res

    def param_set(self, param_name, _value=None, **kwargs):
        """
        Setting parameter. if _value, we inject it directly. if not, we use all extra kwargs
        :param topic_name: name of the topic
        :param _value: optional value
        :param kwargs: each extra kwarg will be put in the value if structure matches
        :return:
        """
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(param_name, unicode):
            param_name = unicodedata.normalize('NFKD', param_name).encode('ascii', 'ignore')

        _value = _value or {}

        if kwargs:
            res = self.param_svc.call(args=(param_name, kwargs,))
        elif _value is not None:
            res = self.param_svc.call(args=(param_name, _value,))
        else:   # if _msg_content is None the request is invalid.
                # just return something to mean False.
            res = 'WRONG SET'

        return res is None  # check if message has been consumed

    def param_get(self, param_name):
        #changing unicode to string ( testing stability of multiprocess debugging )
        if isinstance(param_name, unicode):
            param_name = unicodedata.normalize('NFKD', param_name).encode('ascii', 'ignore')
        res = self.param_svc.call(args=(param_name, None,))
        return res

    def topics(self):
        res = self.topics_svc.call(send_timeout=5000, recv_timeout=10000)  # Need to be generous on timeout in case we are starting up multiprocesses
        return res
        
    def services(self):
        res = self.services_svc.call(send_timeout=5000, recv_timeout=10000)  # Need to be generous on timeout in case we are starting up multiprocesses
        return res

    def params(self):
        res = self.params_svc.call(send_timeout=5000, recv_timeout=10000)  # Need to be generous on timeout in case we are starting up multiprocesses
        return res

    #def listacts(self):
    #    return {}

    # def namespaces(self):
    #    res = self.namespaces_svc.call(args=({},))
    #    return res

    # def interactions(self):
    #    res = self.interactions_svc.call(args=({},))
    #    return res

    # def interaction(self, name):
    #    res = self.interaction_svc.call(args=("",))
    #    return res

    # def has_rocon(self):
    #    res = self.has_rocon_svc.call(args=(False,))
    #    return res

# TODO : test client with Rostful Node ( and detect ROS or not to confirm behvior )
