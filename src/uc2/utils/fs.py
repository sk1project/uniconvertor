#
#  Copyright (C) 2003-2020 by Ihor E. Novikov
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

import glob
import os
import typing as tp


def get_dirs(path: str = '.') -> tp.List[str]:
    """Returns directory list for provided path

    :param path: (str) path to list dirs
    :return: (list) list of found dirs
    """
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


def get_dirs_withpath(path: str = '.') -> tp.List[str]:
    """Returns full path directory list for provided path

    :param path: (str) path to list dirs
    :return: (list) full path list of found dirs
    """
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


def get_files(path: str = '.', ext: str = '*') -> tp.List[str]:
    """Returns file list for provided path

    :param path: (str) path to list files
    :param ext: (str) expected file extension or '*' for any extension
    :return: (list) list of found files
    """

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
                elif name.endswith('.' + ext):
                    lst.append(name)
    return lst


def get_files_withpath(path: str = '.', ext: str = '*') -> tp.List[str]:
    """Returns absolute path file list for provided path

    :param path: (str) path to list files
    :param ext: (str) expected file extension or '*' for any extension
    :return: (list) list of found files with absolute path
    """
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


def get_dirs_tree(path: str = '.') -> tp.List[str]:
    """Return recursive directories list for provided path

    :param path: (str) path to list directories
    :return: (list) recursive directories list
    """
    tree = get_dirs_withpath(path)
    res = [] + tree
    for node in tree:
        subtree = get_dirs_tree(node)
        res += subtree
    return res


def get_files_tree(path='.', ext='*'):
    """Return recursive files list for provided path

    :param path: (str) path to list files
    :param ext: (str) expected file extension or '*' for any extension
    :return: (list) recursive list of found files with absolute path
    """
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

def find_in_path(paths: tp.List[str], filename: str) -> tp.Union[str, None]:
    """Finds a file in one of the directories listed in 'paths'.
       If a file is found, return it's full name, None otherwise.

    :param paths: (list) list of directories
    :param filename: (str) name of file needed to find
    :return: (str|None) absolute file path or None
    """
    for path in paths:
        fullname = os.path.join(path, filename)
        if os.path.isfile(fullname):
            return fullname


def find_files_in_path(paths: tp.List[str], filenames: tp.List[str]) -> tp.Union[str, None]:
    """Finds one of the files listed in FILES in one of the
       directories in PATHS. Return the name of the first one found,
       None if no file is found.

    :param paths: (list) list of directories
    :param filenames: (list) list of file names
    :return: (str|None) absolute file path or None
    """
    for path in paths:
        for filename in filenames:
            fullname = os.path.join(path, filename)
            if os.path.isfile(fullname):
                return fullname


def xclear_dir(path: str) -> None:
    """Removes recursively all files and subdirectories from path.
       Path directory is not removed.

    :param path: (str) path to remove files and directories
    """
    files = get_files_tree(path)
    for file in files:
        if os.path.lexists(file):
            os.remove(file)

    dirs = get_dirs_tree(path)
    for item in dirs:
        if os.path.lexists(item):
            os.rmdir(item)


def xremove_dir(path: str) -> None:
    """Removes recursively all files and subdirectories from path
       including path directory.

    :param path: (str) path to remove files and directories
    """
    xclear_dir(path)
    os.removedirs(path)


def get_file_extension(filepath: str) -> str:
    """Returns file extension without comma.

    :param filepath: (str) path to file
    """
    ext = os.path.splitext(filepath)[1]
    return ext.lower().replace('.', '')
