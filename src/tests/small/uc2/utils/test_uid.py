import base64
import re

from uc2.utils import uid


def test_generate_id():
    id_list = []
    for _i in range(20):
        result = uid.generate_id()
        assert result not in id_list
        assert len(result) == 15
        assert result.isdigit()
        id_list.append(result)


def test_generate_base64_id():
    id_list = []
    for _i in range(20):
        result = uid.generate_base64_id()
        assert result not in id_list
        decoded = base64.b64decode(result.encode()).decode()
        assert len(decoded) == 15
        assert decoded.isdigit()
        id_list.append(result)


def test_generate_guid():
    pattern = re.compile('........-....-....-....-............')
    id_list = []
    for _i in range(20):
        result = uid.generate_guid()
        assert result not in id_list
        assert len(result) == 36
        assert pattern.match(result)
        id_list.append(result)
