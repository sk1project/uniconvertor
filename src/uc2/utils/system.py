#
#  Copyright (C) 2010, 2011, 2020 by Ihor E. Novikov
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

import platform

WINDOWS = 'Windows'
LINUX = 'Linux'
MACOS = 'Darwin'
GENERIC = 'generic'


def get_os_family() -> str:
    """Detects OS type and returns module predefined platform name.
       The function is used for all platform dependent issues.
    """
    name = platform.system()
    return name if name in (LINUX, WINDOWS, MACOS) else GENERIC


IS_WINDOWS: bool = get_os_family() == WINDOWS
IS_LINUX: bool = get_os_family() == LINUX
IS_MACOS: bool = get_os_family() == MACOS

P32BIT = '32bit'
P64BIT = '64bit'
P128BIT = '128bit'
PXXBIT = 'unknown'


def get_os_arch() -> str:
    """Detects OS architecture and returns module predefined architecture type.
    """
    arch = platform.architecture()[0]
    return arch if arch in (P32BIT, P64BIT, P128BIT) else PXXBIT


WINXP = 'XP'
WINVISTA = 'Vista'
WIN7 = '7'
WIN8 = '8'
WIN8_1 = '8.1'
WIN10 = '10'
WIN_VERSIONS = [WINXP, WINVISTA, WIN7, WIN8, WIN8_1, WIN10]
WINOTHER = 'WinOther'

UBUNTU = 'Ubuntu'
MINT = 'LinuxMint'
DEBIAN = 'debian'
MANDRIVA = 'mandrake'
MAGEIA = 'mageia'
FEDORA = 'fedora'
SUSE = 'SuSE'
MXLINUX = 'MX'
EOS = 'elementary'
ARCHLINUX = 'arch'
LINUX_DISTROS = [UBUNTU, MINT, DEBIAN, MANDRIVA, MAGEIA, FEDORA, SUSE, MXLINUX, EOS, ARCHLINUX]
LINUXOTHER = 'LinuxOther'

MAC_MAVERICKS = '10.9'
MAC_YOSEMITE = '10.10'
MAC_EL_CAPITAN = '10.11'
MAC_SIERRA = '10.12'
MAC_HIGH_SIERRA = '10.13'
MAC_MOJAVE = '10.14'
MAC_CATALINA = '10.15'
MAC_BIG_SUR = '11.0'
MAC_VERSIONS = [MAC_MAVERICKS, MAC_YOSEMITE, MAC_EL_CAPITAN, MAC_SIERRA, MAC_HIGH_SIERRA, MAC_MOJAVE,
                MAC_CATALINA, MAC_BIG_SUR]
MACOTHER = 'MacOther'

UNIX = 'unix'


def get_os_name() -> str:
    """Detects OS name and returns module predefined constant.
    """
    if get_os_family() == WINDOWS:
        release = platform.release()
        return release if release in WIN_VERSIONS else WINOTHER

    elif get_os_family() == LINUX:
        release = platform.platform()
        for distro in LINUX_DISTROS:
            if '-%s-' % distro in release:
                return distro
        return LINUXOTHER

    elif get_os_family() == MACOS:
        release = platform.mac_ver()[0]
        return release if release in MAC_VERSIONS else MACOTHER

    return UNIX
