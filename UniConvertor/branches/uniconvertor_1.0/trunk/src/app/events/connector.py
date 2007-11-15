# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#	The Connector
#

from types import MethodType

from app.events.skexceptions import SketchInternalError
from warn import warn_tb, INTERNAL


class ConnectorError(SketchInternalError):
	pass

class Connector:

	def __init__(self):
		self.connections = {}

	def Connect(self, object, channel, function, args):
		idx = id(object)
		if self.connections.has_key(idx):
			channels = self.connections[idx]
		else:
			channels = self.connections[idx] = {}

		if channels.has_key(channel):
			receivers = channels[channel]
		else:
			receivers = channels[channel] = []

		info = (function, args)
		try:
			receivers.remove(info)
		except ValueError:
			pass
		receivers.append(info)

	def Disconnect(self, object, channel, function, args):
		try:
			receivers = self.connections[id(object)][channel]
		except KeyError:
			raise ConnectorError, \
					'no receivers for channel %s of %s' % (channel, object)
		try:
			receivers.remove((function, args))
		except ValueError:
			raise ConnectorError,\
			'receiver %s%s is not connected to channel %s of %s' \
			% (function, args, channel, object)

		if not receivers:
			# the list of receivers is empty now, remove the channel
			channels = self.connections[id(object)]
			del channels[channel]
			if not channels:
				# the object has no more channels
				del self.connections[id(object)]

	def Issue(self, object, channel, *args):
		#print object, channel, args
		try:
			receivers = self.connections[id(object)][channel]
		except KeyError:
			return
		for func, fargs in receivers:
			try:
				apply(func, args + fargs)
			except:
				warn_tb(INTERNAL, "%s.%s: %s%s", object, channel, func, fargs)

	def RemovePublisher(self, object):
		i = id(object)
		if self.connections.has_key(i):
			del self.connections[i]
		# don't use try: del ... ; except KeyError here. That would create a
		# new reference of object in a traceback object and this method should
		# be callable from a __del__ method (at least for versions prior
		# Python 1.5)

	def HasSubscribers(self, object):
		return self.connections.has_key(id(object))

	def print_connections(self):
		# for debugging
		for id, channels in self.connections.items():
			for name, subscribers in channels.items():
				print id, name
				for func, args in subscribers:
					if type(func) == MethodType:
						print '\tmethod %s of %s' % (func.im_func.func_name,
														func.im_self)
					else:
						print '\t', func



_the_connector = Connector()

Connect = _the_connector.Connect
Issue = _the_connector.Issue
RemovePublisher = _the_connector.RemovePublisher
Disconnect = _the_connector.Disconnect
def Subscribe(channel, function, *args):
	return Connect(None, channel, function, args)


class Publisher:

	ignore_issue = 0

	def __del__(self):
		# the new finalization code in 1.5.1 might bind RemovePublisher
		# to None before all objects derived from Publisher are deleted...
		if RemovePublisher is not None:
			RemovePublisher(self)

	def Subscribe(self, channel, func, *args):
		Connect(self, channel, func, args)

	def Unsubscribe(self, channel, func, *args):
		Disconnect(self, channel, func, args)

	def issue(self, channel, *args):
		if not self.ignore_issue:
			apply(Issue, (self, channel,) + args)

	def Destroy(self):
		RemovePublisher(self)


class QueueingPublisher(Publisher):

	def __init__(self):
		self.clear_message_queue()

	def queue_message(self, channel, *args):
		# Put message in the queue. If it is already queued put it at
		# the end. This is done to make certain that no channel gets
		# called twice between two calls to flush_message_queue. If the
		# order of channel invocation is important two or more queues
		# should be used.
		message = (channel, args)
		if message not in self.message_queue:
			self.message_queue.append(message)

	def flush_message_queue(self):
		# Issue all queued messages and make the queue empty
		#
		# Issueing messages might result in new messages being queued.
		# This does not happen in sketch yet (Jul 1997) but let's hope
		# that we don't get infinite loops here...
		while self.message_queue:
			queue = self.message_queue
			self.message_queue = []
			for channel, args in queue:
				apply(Issue, (self, channel) + args)

	def clear_message_queue(self):
		self.message_queue = []

