# -*- coding: utf-8 -*-
"""
    shop.singals
"""
from blinker import Namespace

_signals = Namespace()

#: Sent when a cart's user change
cart_user_changed = _signals.signal('cart-user-changed')
