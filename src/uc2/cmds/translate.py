# -*- coding: utf-8 -*-
#
#  Copyright (C) 2019 by Igor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import copy
import glob
import logging
import os

from uc2 import events, uc2const, msgconst
from uc2.formats import get_loader, get_saver, get_saver_by_id
from uc2.utils.mixutils import echo

LOG = logging.getLogger(__name__)
SAVER_IDS = uc2const.PALETTE_SAVERS + uc2const.MODEL_SAVERS \
            + uc2const.BITMAP_SAVERS


def normalize_options(options):
    for key in ('verbose', 'format', 'recursive', 'dry-run'):
        if key in options:
            options.pop(key)

    keys = options.keys()
    for key in keys:
        if '-' in key:
            options.pop(key)


def convert(appdata, files, options):
    dry_run = bool(options.get('dry-run'))
    normalize_options(options)

    msg = 'Translation of "%s" into "%s"' % (files[0], files[1])
    events.emit(events.MESSAGES, msgconst.JOB, msg)

    # Define saver -----------------------------------------
    sid = options.get('format', '').lower()
    if sid and sid in SAVER_IDS:
        saver_id = sid
        saver = get_saver_by_id(saver_id)
    else:
        saver, saver_id = get_saver(files[1], return_id=True)
    if saver is None:
        msg = 'Output file format of "%s" is unsupported.' % files[1]
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        msg2 = 'Translation is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg2)
        raise Exception(msg)

    # Define loader -----------------------------------------
    loader, loader_id = get_loader(files[0], return_id=True)
    if loader is None:
        msg = 'Input file format of "%s" is unsupported.' % files[0]
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        msg2 = 'Translation is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg2)
        raise Exception(msg)

    if dry_run:
        return

    # File loading -----------------------------------------
    doc = None
    try:
        if loader_id in uc2const.PALETTE_LOADERS and \
                saver_id in uc2const.PALETTE_SAVERS:
            doc = loader(appdata, files[0], convert=True, **options)
        else:
            doc = loader(appdata, files[0], **options)
    except Exception:
        msg = 'Error while loading "%s"' % files[0]
        msg += 'The file may be corrupted or contains unknown file format.'
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        LOG.exception(msg)
        msg = 'Loading is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg)
        raise

    # File saving -----------------------------------------
    if doc is not None:
        try:
            if loader_id in uc2const.PALETTE_LOADERS and \
                    saver_id in uc2const.PALETTE_SAVERS:
                saver(doc, files[1], translate=False, convert=True,
                      **options)
            else:
                saver(doc, files[1], **options)
        except Exception:
            msg = 'Error while translation and saving "%s"' % files[0]
            events.emit(events.MESSAGES, msgconst.ERROR, msg)

            LOG.exception(msg)
            msg2 = 'Translation is interrupted'
            events.emit(events.MESSAGES, msgconst.STOP, msg2)
            raise
    else:
        msg = 'Error creating model for "%s"' % files[0]
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        msg2 = 'Translation is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg2)
        raise Exception(msg)

    doc.close()
    msg = 'Translation is successful'
    events.emit(events.MESSAGES, msgconst.OK, msg)


def _get_saver_extension(options):
    if 'format' not in options:
        msg = 'Output file format is not defined.'
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        msg2 = 'Translation is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg2)
        raise Exception(msg)

    sid = options.get('format', '').lower()
    if sid not in SAVER_IDS:
        msg = 'Output file format is not supported.'
        events.emit(events.MESSAGES, msgconst.ERROR, msg)

        msg2 = 'Translation is interrupted'
        events.emit(events.MESSAGES, msgconst.STOP, msg2)
        raise Exception(msg)
    return uc2const.FORMAT_EXTENSION[sid][0]


def _get_filelist(path, subpath, wildcard, recursive=False):
    dir_path = os.path.join(path, subpath)
    wildcard_path = os.path.join(dir_path, wildcard)
    filelist = [(item, subpath, os.path.basename(item).split('.', 1)[0])
                for item in glob.glob(wildcard_path) if os.path.isfile(item)]

    if recursive:
        dirs = [item for item in os.listdir(dir_path)
                if os.path.isdir(os.path.join(dir_path, item))]
        for item in dirs:
            filelist += _get_filelist(
                path, os.path.join(subpath, item), wildcard, recursive)
    return filelist


def multiple_convert(appdata, files, options):
    saver_ext = _get_saver_extension(options)
    verbose = bool(options.get('verbose'))
    verbose_short = bool(options.get('verbose-short'))

    filelist = files[:-1]
    dir_path = files[-1]
    for filepath in filelist:
        if not os.path.exists(filepath):
            msg = 'File "%s" is not found' % filepath
            events.emit(events.MESSAGES, msgconst.STOP, msg)
            continue
        filename = os.path.basename(filepath).split('.', 1)[0]
        out_filepath = os.path.join(dir_path, '%s.%s' % (filename, saver_ext))
        kw = copy.deepcopy(options)
        try:
            convert(appdata, (filepath, out_filepath), kw)
            if verbose:
                echo()
            elif verbose_short:
                echo('Translation of "%s"' % filepath)
                echo('into "%s" ...[  OK  ]\n' % out_filepath)
        except Exception:
            if verbose_short:
                echo('Translation of "%s"' % filepath)
                echo('into "%s" ...[ FAIL ]\n' % out_filepath)


def wildcard_convert(appdata, files, options):
    saver_ext = _get_saver_extension(options)
    verbose = bool(options.get('verbose'))
    verbose_short = bool(options.get('verbose-short'))

    path = os.path.dirname(files[0])
    wildcard = os.path.basename(files[0])

    filelist = _get_filelist(path, '', wildcard, bool(options.get('recursive')))
    if not filelist:
        msg = 'There are not files for requested wildcard "%s"' % wildcard
        events.emit(events.MESSAGES, msgconst.STOP, msg)
        return

    for filepath, subpath, filename in filelist:
        dir_path = os.path.join(files[1], subpath)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        out_filepath = os.path.join(dir_path, '%s.%s' % (filename, saver_ext))
        kw = copy.deepcopy(options)
        try:
            convert(appdata, (filepath, out_filepath), kw)
            if verbose:
                echo()
            elif verbose_short:
                echo('Translation of "%s"' % filepath)
                echo('into "%s" ...[  OK  ]\n' % out_filepath)
        except Exception:
            if verbose_short:
                echo('Translation of "%s"' % filepath)
                echo('into "%s" ...[ FAIL ]\n' % out_filepath)
