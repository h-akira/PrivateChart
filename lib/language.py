#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Dictionary:
  JP2EN = {
    "成行":"market",
    "通常":"normal",
    "OCO":"OCO",
    "IFD-OCO":"IFD-OCO",
    "新規":"new",
    "決済":"settlement",
    "買":"buy",
    "売":"sell",
    "取消済":"canceled",
    "受付済":"accepted",
    "約定済":"executed",
    "指値":"limit",
    "逆指値":"stop"
  }
  EN2JP = {v:k for k,v in JP2EN.items()}
