from uc2.libpango import langs


def test_check_lang():
    assert langs.check_lang('٢٠٢٠ م جرافيكا', (langs.ARABIC,))
    assert not langs.check_lang('Wszystko dobrze', (langs.ARABIC,))


def test_check_maynmar():
    assert langs.check_maynmar('ကောင်းပါပြီ')
    assert not langs.check_maynmar('Wszystko dobrze')


def test_check_arabic():
    assert langs.check_arabic('٢٠٢٠ م جرافيكا')
    assert not langs.check_arabic('Wszystko dobrze')
