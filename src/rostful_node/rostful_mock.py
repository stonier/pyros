from __future__ import absolute_import

import ast
import json
import os
import logging
import time

# python protocol should be usable without ROS.
from .rostful_prtcl import MsgBuild, Topic, Service
from multiprocessing import Pipe
import threading
"""
Mock Interface in pure python ( No ROS needed ).
"""

class RostfulMock(object):

    def __init__(self):
        self._topic_msg = {}  # storage for the echo topic
        self._stop_event = None  # stop_event to signal the thread for soft shutdown
        self._spinner = None  # thread instance
        pass

    # These should match the design of RostfulClient and Protocol so we are consistent between pipe and python API
    def msg_build(self, name):
        msg = str()
        return msg

    # a simple echo topic
    def topic(self, name, msg_content=None):
        msg = msg_content
        if msg_content:
            self._topic_msg[name] = msg_content
            msg = None  # consuming the message
        else:
            msg = self._topic_msg.get(name, None)
        return msg

    # a simple echo service
    def service(self, name, rqst_content=None):
        resp_content = rqst_content
        return resp_content

    def _process_pipe_msg(self, pipe_conn):
        rqst = pipe_conn.recv()
        resp = rqst  # if problem we send back the exact same request message.
        # here we need to make sure we always send something back ( so the client can block safely )
        try:
            if isinstance(rqst, MsgBuild):
                resp = MsgBuild(
                    name=rqst.name,
                    msg_content=self.msg_build(rqst.name)
                )
            elif isinstance(rqst, Topic):
                resp = Topic(
                    name=rqst.name,
                    msg_content=self.topic(rqst.name, rqst.msg_content)
                )
            elif isinstance(rqst, Service):
                resp = Service(
                    name=rqst.name,
                    rqst_content=rqst.rqst_content,
                    resp_content=self.service(rqst.name, rqst.rqst_content)
                )

        finally:
            # to make sure we always return something, no matter what
            pipe_conn.send(resp)

    def spin(self, pipe_conn, stop_event):
        """
        Spinning, processing commands arriving in the queue
        :return:
        """
        # check if INITED ( using Context or not )

        logging.debug("mock entering spin(), pid[%s]", os.getpid())
        try:
            # we should exit if we lose connection or stop_event disappear.
            while pipe_conn and stop_event and not stop_event.is_set():
                try:
                    if pipe_conn.poll(0.5):
                        self._process_pipe_msg(pipe_conn)
                    else:  # no data, no worries.
                        pass
                except EOFError:  # empty pipe, no worries.
                    pass
                except Exception, e:
                    raise e

        # Just in case spin() is run synchronously.
        # If run asynchronously these can only be caught in the main thread
        except KeyboardInterrupt:
            logging.debug("Keyboard Interrupt , shutting down")
            # trigger shutdown
        except SystemExit:
            logging.debug("System Exit , shutting down")

    def async_spin(self):
        """
        Starts spinning in another thread and returns the pipe connection to send commands to
        :return: pipe end used to communicate with the thread.
        """
        self._stop_event = threading.Event()
        pipe_conn, other_end = Pipe()
        self._spinner = threading.Thread(target=self.spin, args=(pipe_conn, self._stop_event,))
        self._spinner.start()
        return other_end

    # parent thread needs to call this to terminate the thread gracefully
    def async_stop(self):
        if self._stop_event:
            self._stop_event.set()
        if self._spinner:
            self._spinner.join()

