import pytest

from shop.utils import json_ld_dict


def test_sample_with_dict():
    data = {
        'apple': 'a',
        'ball': 'b',
    }
    ld_dict = json_ld_dict(data)
    assert ld_dict.__html__()
