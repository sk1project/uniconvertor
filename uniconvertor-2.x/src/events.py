# -*- coding: utf-8 -*-

# Copyright (C) 2011 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

"""
The package provides Qt-like signal-slot functionality
for internal events processing.
"""

#Signal channels

CONFIG_MODIFIED = ['CONFIG_MODIFIED']

def connect(channel, receiver):
	"""
	Connects signal receive method
	to provided channel. 
	"""
	if callable(receiver):
		try:
			channel.append(receiver)
		except:
			print "Cannot connect to channel:", channel, "receiver:", receiver
			
def disconnect(channel, receiver):
	"""
	Disconnects signal receive method
	from provided channel. 
	"""
	if callable(receiver):
		try:
			channel.remove(receiver)
		except:
			print "Cannot disconnect from channel:", channel, "receiver:", receiver
			
def emit(channel, *args):
	"""
	Sends signal to all receivers in channel.
	"""
#	print 'signal', channel[0]
	try:
		for receiver in channel[1:]:
			try:
				if callable(receiver):
					receiver(args)
			except:
				pass
	except:
		print "Cannot send signal to channel:", channel
		





