import struct

import pytest

from uc2.utils import structutils


def test_byte2py_int():
    assert structutils.byte2py_int(b'a') == 97
    with pytest.raises(struct.error):
        structutils.byte2py_int(b'aa')


def test_py_int2byte():
    assert structutils.py_int2byte(97) == b'a'
    with pytest.raises(struct.error):
        structutils.py_int2byte(297)


def test_word2py_int():
    assert structutils.word2py_int(b'ab') == 25185
    assert structutils.word2py_int(b'ab', True) == 24930
    with pytest.raises(struct.error):
        structutils.word2py_int(b'abc')
    with pytest.raises(struct.error):
        structutils.word2py_int(b'a')


def test_signed_word2py_int():
    assert structutils.signed_word2py_int(b'\xaa\xff') == -86
    assert structutils.signed_word2py_int(b'\xaa\xff', True) == -21761
    with pytest.raises(struct.error):
        structutils.signed_word2py_int(b'abc')
    with pytest.raises(struct.error):
        structutils.signed_word2py_int(b'a')


def test_py_int2word():
    assert structutils.py_int2word(25185) == b'ab'
    assert structutils.py_int2word(24930, True) == b'ab'
    with pytest.raises(struct.error):
        structutils.py_int2word(66535)


def test_py_int2signed_word():
    assert structutils.py_int2signed_word(-25185) == b'\x9f\x9d'
    assert structutils.py_int2signed_word(24930, True) == b'ab'
    with pytest.raises(struct.error):
        structutils.py_int2signed_word(33768)


def test_dword2py_int():
    assert structutils.dword2py_int(b'abcd') == 1684234849
    assert structutils.dword2py_int(b'abcd', True) == 1633837924
    with pytest.raises(struct.error):
        structutils.dword2py_int(b'abcde')
    with pytest.raises(struct.error):
        structutils.dword2py_int(b'abc')
    with pytest.raises(struct.error):
        structutils.dword2py_int(b'a')


def test_signed_dword2py_int():
    assert structutils.signed_dword2py_int(b'\x9f\x9d\x9f\x9d') == -1650483809
    assert structutils.signed_dword2py_int(b'\x9f\x9d\x9f\x9d', True) == -1617059939
    with pytest.raises(struct.error):
        structutils.signed_dword2py_int(b'abcde')
    with pytest.raises(struct.error):
        structutils.signed_dword2py_int(b'abc')
    with pytest.raises(struct.error):
        structutils.signed_dword2py_int(b'a')


def test_py_int2dword():
    assert structutils.py_int2dword(1684234849) == b'abcd'
    assert structutils.py_int2dword(1633837924, True) == b'abcd'
    with pytest.raises(struct.error):
        structutils.py_int2dword(2**33)


def test_py_int2signed_dword():
    assert structutils.py_int2signed_dword(-1650483809) == b'\x9f\x9d\x9f\x9d'
    assert structutils.py_int2signed_dword(-1617059939, True) == b'\x9f\x9d\x9f\x9d'
    with pytest.raises(struct.error):
        structutils.py_int2dword(2**32)


def test_pair_dword2py_int():
    assert len(structutils.pair_dword2py_int(b'abcddcba')) == 2
    assert structutils.pair_dword2py_int(b'abcddcba') == (1684234849, 1633837924)


def test_py_float2float():
    assert structutils.py_float2float(1.2) == b'\x9a\x99\x99?'
    assert structutils.py_float2float(1.2, True) == b'?\x99\x99\x9a'


def test_float2py_float():
    assert round(structutils.float2py_float(b'\x9a\x99\x99?'), 5) == 1.2
    assert round(structutils.float2py_float(b'?\x99\x99\x9a', True), 5) == 1.2


def test_double2py_float():
    assert structutils.double2py_float(b'abcdabcd') == 3.835461081268274e+175
    assert structutils.double2py_float(b'abcdabcd', True) == 1.2926117739473244e+161


def test_py_float2double():
    assert structutils.py_float2double(1.2) == b'333333\xf3?'
    assert structutils.py_float2double(1.2, True) == b'?\xf3333333'


def test_get_chunk_size():
    assert structutils.get_chunk_size(b'ccba') == 1633837924
    assert structutils.get_chunk_size(b'dcba') == 1633837924
    assert structutils.get_chunk_size(b'bcba') == 1633837922
    assert structutils.get_chunk_size(b'acba') == 1633837922


def test_uint16_be():
    assert structutils.uint16_be(b'ab') == 24930
