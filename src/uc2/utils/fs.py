# -*- coding: utf-8 -*-
#
#  Copyright (C) 2003-2011 by Igor E. Novikov
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

#
#  File system related functions used in various places...
#

import os


# Return directory list for provided path

def get_dirs(path='.'):
    lst = []
    names = []
    if path:
        if os.path.isdir(path):
            try:
                names = os.listdir(path)
            except os.error:
                return []
        names.sort()
        for name in names:
            if os.path.isdir(os.path.join(path, name)):
                lst.append(name)
        return lst


def get_dirs_withpath(path='.'):
    lst = []
    names = []
    if os.path.isdir(path):
        try:
            names = os.listdir(path)
        except os.error:
            return names
    names.sort()
    for name in names:
        if os.path.isdir(os.path.join(path, name)) and not name == '.svn':
            lst.append(os.path.join(path, name))
    return lst


# Return file list for provided path
def get_files(path='.', ext='*'):
    lst = []
    names = []
    if path:
        if os.path.isdir(path):
            try:
                names = os.listdir(path)
            except os.error:
                return []
        names.sort()
        for name in names:
            if not os.path.isdir(os.path.join(path, name)):
                if ext == '*':
                    lst.append(name)
                elif '.' + ext == name[-1 * (len(ext) + 1):]:
                    lst.append(name)
    return lst


# Return full file names list for provided path
def get_files_withpath(path='.', ext='*'):
    import glob
    if ext:
        if ext == '*':
            lst = glob.glob(os.path.join(path, "*." + ext))
            lst += glob.glob(os.path.join(path, "*"))
            lst += glob.glob(os.path.join(path, ".*"))
        else:
            lst = glob.glob(os.path.join(path, "*." + ext))
    else:
        lst = glob.glob(os.path.join(path, "*"))
    lst.sort()
    result = []
    for file in lst:
        if os.path.isfile(file):
            result.append(file)
    return result


# Return recursive directories list for provided path
def get_dirs_tree(path='.'):
    tree = get_dirs_withpath(path)
    res = [] + tree
    for node in tree:
        subtree = get_dirs_tree(node)
        res += subtree
    return res


# Return recursive files list for provided path
def get_files_tree(path='.', ext='*'):
    tree = []
    dirs = [path, ]
    dirs += get_dirs_tree(path)
    for item in dirs:
        lst = get_files_withpath(item, ext)
        lst.sort()
        tree += lst
    return tree


#
# Filename manipulations
#

def find_in_path(paths, file):
    """
    The function finds a file FILE in one of the directories listed in PATHS.
    If a file is found, return its full name, None otherwise.
    """
    for path in paths:
        fullname = os.path.join(path, file)
        if os.path.isfile(fullname):
            return fullname


def find_files_in_path(paths, files):
    """
    The function finds one of the files listed in FILES in one of the
    directories in PATHS. Return the name of the first one found,
    None if no file is found.
    """
    for path in paths:
        for file in files:
            fullname = os.path.join(path, file)
            if os.path.isfile(fullname):
                return fullname


def xclear_dir(path):
    """
    Remove recursively all files and subdirectories from path.
    path directory is not removed.
    """
    files = get_files_tree(path)
    for file in files:
        if os.path.lexists(file):
            os.remove(file)

    dirs = get_dirs_tree(path)
    for item in dirs:
        if os.path.lexists(item):
            os.rmdir(item)


def xremove_dir(path):
    """
    Remove recursively all files and subdirectories from path
    including path directory.
    """
    xclear_dir(path)
    os.removedirs(path)


def get_file_extension(path):
    """
    Returns file extension without comma.
    """
    ext = os.path.splitext(path)[1]
    ext = ext.lower().replace('.', '')
    return ext
