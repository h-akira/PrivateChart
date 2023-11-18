#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

def market_open():
  DIFF_JST_FROM_UTC = 9
  now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
  num = now.weekday()
  if 1 <= num <= 4:
    return True
  elif num == 0 and now.hour >= 7:  
    return True
  elif num == 5 and now.hour < 7:
    return True
  else:
    return False
