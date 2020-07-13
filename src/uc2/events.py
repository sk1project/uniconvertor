# -*- coding: utf-8 -*-
#
#  Copyright (C) 2011-2020 by Ihor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import typing as tp

LOG = logging.getLogger(__name__)
ChannelType = tp.List[tp.Union[str, tp.Callable]]

"""
This module provides event-receiver functionality
for internal events processing.

Signal arguments:
CONFIG_MODIFIED   attr, value - modified config field
FILTER_INFO       msg, position - info message and progress in range 0.0-1.0
MESSAGES          msg_type, msg - message type and message text

"""

# Signal flags

CANCEL_OPERATION = False

# Event channels

CONFIG_MODIFIED: ChannelType = ['CONFIG_MODIFIED']
FILTER_INFO: ChannelType = ['FILTER_INFO']
MESSAGES: ChannelType = ['MESSAGES']


def connect(channel: ChannelType, receiver: tp.Callable) -> None:
    """Connects signal receive method to provided channel.
    """
    if callable(receiver):
        # noinspection PyBroadException
        try:
            channel.append(receiver)
        except Exception:
            LOG.exception('Cannot connect <%s> receiver to <%s> channel', receiver, channel)


def disconnect(channel: ChannelType, receiver: tp.Callable) -> None:
    """Disconnects signal receive method from provided channel.
    """
    if receiver in channel:
        # noinspection PyBroadException
        try:
            channel.remove(receiver)
        except Exception:
            LOG.exception('Cannot disconnect <%s> receiver from <%s> channel', receiver, channel)


def emit(channel: ChannelType, *args: tp.Any) -> None:
    """Sends event to all receivers in channel.
    """
    for receiver in channel[1:]:
        # noinspection PyBroadException
        try:
            if callable(receiver):
                receiver(*args)
        except Exception:
            LOG.exception('Error calling <%s> receiver with %s', receiver, args)
            continue


def clean_channel(channel: ChannelType) -> None:
    """Cleans channel queue.
    """
    channel[:] = channel[:1]


def clean_all_channels() -> None:
    """Cleans all channels.
    """
    for item in (CONFIG_MODIFIED, MESSAGES, FILTER_INFO):
        clean_channel(item)
