import base64
import re
import struct

import pytest

from uc2.utils import binutils


def test_generate_id():
    id_list = []
    for _i in range(20):
        result = binutils.generate_id()
        assert result not in id_list
        assert len(result) == 15
        assert result.isdigit()
        id_list.append(result)


def test_generate_base64_id():
    id_list = []
    for _i in range(20):
        result = binutils.generate_base64_id()
        assert result not in id_list
        decoded = base64.b64decode(result.encode()).decode()
        assert len(decoded) == 15
        assert decoded.isdigit()
        id_list.append(result)


def test_generate_guid():
    pattern = re.compile('........-....-....-....-............')
    id_list = []
    for _i in range(20):
        result = binutils.generate_guid()
        assert result not in id_list
        assert len(result) == 36
        assert pattern.match(result)
        id_list.append(result)


def test_byte2py_int():
    assert binutils.byte2py_int(b'a') == 97
    with pytest.raises(struct.error):
        binutils.byte2py_int(b'aa')


def test_py_int2byte():
    assert binutils.py_int2byte(97) == b'a'
    with pytest.raises(struct.error):
        binutils.py_int2byte(297)


def test_word2py_int():
    assert binutils.word2py_int(b'ab') == 25185
    assert binutils.word2py_int(b'ab', True) == 24930
    with pytest.raises(struct.error):
        binutils.word2py_int(b'abc')
    with pytest.raises(struct.error):
        binutils.word2py_int(b'a')


def test_signed_word2py_int():
    assert binutils.signed_word2py_int(b'\xaa\xff') == -86
    assert binutils.signed_word2py_int(b'\xaa\xff', True) == -21761
    with pytest.raises(struct.error):
        binutils.signed_word2py_int(b'abc')
    with pytest.raises(struct.error):
        binutils.signed_word2py_int(b'a')


def test_py_int2word():
    assert binutils.py_int2word(25185) == b'ab'
    assert binutils.py_int2word(24930, True) == b'ab'
    with pytest.raises(struct.error):
        binutils.py_int2word(66535)


def test_py_int2signed_word():
    assert binutils.py_int2signed_word(-25185) == b'\x9f\x9d'
    assert binutils.py_int2signed_word(24930, True) == b'ab'
    with pytest.raises(struct.error):
        binutils.py_int2signed_word(33768)


def test_dword2py_int():
    assert binutils.dword2py_int(b'abcd') == 1684234849
    assert binutils.dword2py_int(b'abcd', True) == 1633837924
    with pytest.raises(struct.error):
        binutils.dword2py_int(b'abcde')
    with pytest.raises(struct.error):
        binutils.dword2py_int(b'abc')
    with pytest.raises(struct.error):
        binutils.dword2py_int(b'a')


def test_signed_dword2py_int():
    assert binutils.signed_dword2py_int(b'\x9f\x9d\x9f\x9d') == -1650483809
    assert binutils.signed_dword2py_int(b'\x9f\x9d\x9f\x9d', True) == -1617059939
    with pytest.raises(struct.error):
        binutils.signed_dword2py_int(b'abcde')
    with pytest.raises(struct.error):
        binutils.signed_dword2py_int(b'abc')
    with pytest.raises(struct.error):
        binutils.signed_dword2py_int(b'a')


def test_py_int2dword():
    assert binutils.py_int2dword(1684234849) == b'abcd'
    assert binutils.py_int2dword(1633837924, True) == b'abcd'
    with pytest.raises(struct.error):
        binutils.py_int2dword(2**33)


def test_py_int2signed_dword():
    assert binutils.py_int2signed_dword(-1650483809) == b'\x9f\x9d\x9f\x9d'
    assert binutils.py_int2signed_dword(-1617059939, True) == b'\x9f\x9d\x9f\x9d'
    with pytest.raises(struct.error):
        binutils.py_int2dword(2**32)


def test_pair_dword2py_int():
    assert len(binutils.pair_dword2py_int(b'abcddcba')) == 2
    assert binutils.pair_dword2py_int(b'abcddcba') == (1684234849, 1633837924)


def test_py_float2float():
    assert binutils.py_float2float(1.2) == b'\x9a\x99\x99?'
    assert binutils.py_float2float(1.2, True) == b'?\x99\x99\x9a'


def test_float2py_float():
    assert round(binutils.float2py_float(b'\x9a\x99\x99?'), 5) == 1.2
    assert round(binutils.float2py_float(b'?\x99\x99\x9a', True), 5) == 1.2


def test_double2py_float():
    assert binutils.double2py_float(b'abcdabcd') == 3.835461081268274e+175
    assert binutils.double2py_float(b'abcdabcd', True) == 1.2926117739473244e+161


def test_py_float2double():
    assert binutils.py_float2double(1.2) == b'333333\xf3?'
    assert binutils.py_float2double(1.2, True) == b'?\xf3333333'


def test_get_chunk_size():
    assert binutils.get_chunk_size(b'ccba') == 1633837924
    assert binutils.get_chunk_size(b'dcba') == 1633837924
    assert binutils.get_chunk_size(b'bcba') == 1633837922
    assert binutils.get_chunk_size(b'acba') == 1633837922


def test_uint16_be():
    assert binutils.uint16_be(b'ab') == 24930
