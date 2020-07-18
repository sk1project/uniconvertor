#
#  Copyright (C) 2018, 2020 by Ihor E. Novikov
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

import gettext
import os
import typing as tp

SYS_LANG = 'system'


class MsgTranslator:
    """Represents message translator object,
       Depending on initialization, it uses either gettex or dummy translator.
    """
    translate: tp.Callable

    def __init__(self, textdomain: str = None, msgs_path: str = None, lang: str = SYS_LANG) -> None:
        """Creates MsgTranslator object

        :param textdomain: (str) application domain (usually application name)
        :param msgs_path: (str) path to folder with translation messages
        :param lang: (str) language identifier like 'pl', 'pt', 'es' etc.
        """
        self.translate = self.dummy_translate
        if textdomain and msgs_path:
            self.set_lang(textdomain, msgs_path, lang)

    @staticmethod
    def dummy_translate(msg: str) -> str:
        """Stub for unknown or English locale

        :param msg: (str) original message
        :return: (str) the same original message
        """
        return msg

    def set_lang(self, textdomain: str = None, msgs_path: str = None, lang: str = SYS_LANG) -> None:
        """Sets full featured gettext translator for MsgTranslator object

        :param textdomain: (str) application domain (usually application name)
        :param msgs_path: (str) path to folder with translation messages
        :param lang: (str) locale identifier like 'pl', 'pt', 'es' etc.
        """
        if lang != 'en' and os.path.exists(msgs_path):
            if lang != SYS_LANG:
                os.environ['LANGUAGE'] = lang
            gettext.bindtextdomain(textdomain, msgs_path)
            gettext.textdomain(textdomain)
            self.translate = gettext.gettext

    def __call__(self, msg: str) -> str:
        """MsgTranslator object callable method

        :param msg: (str) original message
        :return: (str) translated message
        """
        return self.translate(msg)
