#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2023-05-26 23:28:35

# Import
import sys
import os
import numpy
import time
# import selenium
import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def GMO_html2df(html):
  bs = BeautifulSoup(html, 'html.parser')
  table = bs.find('table', attrs={"class":"search-result-table"})
  thead = table.find('thead')
  ths = thead.tr.find_all('th')
  columns_jp = []
  for th in ths:
    columns_jp.append(th.text)
  tbody = table.find('tbody')
  trs = tbody.find_all('tr')
  data = []
  for tr in trs:
    row = []
    for td in tr.find_all('td'):
      row.append(td.text)
    data.append(row)
  df = pd.DataFrame(data=data,columns=columns_jp)
  df.replace('', numpy.nan, inplace=True)
  df["order_number"] = df["注文番号"].astype(pd.Int64Dtype())
  df["pair"] = df["通貨ペア"]
  df["order_type"] = df["注文タイプ"]
  df["kind"] = df["\n取引種類\n\n売買\n"].str.split(expand=True)[0].str.strip()
  df["buy_sell"] = df["\n取引種類\n\n売買\n"].str.split(expand=True)[1].str.strip()
  df["quantity"] = df["取引数量"]
  df["state and revocation reason"] = df["状態失効理由"]
  df["order_datetime"] = pd.to_datetime(df["注文日時有効期限"].str[:17], format="%y/%m/%d %H:%M:%S")
  df["order_rate"] = df["注文レート[執行条件]現在値"].str.split("[\[\]]",expand=True)[0].astype(float)
  df["condition"] = df["注文レート[執行条件]現在値"].str.split("[\[\]]",expand=True)[1]  # 指値，逆指値，成行
  df["execution_rate"] = df["約定レート "].astype(float)
  # df["execution_datetime"] = df["約定日時受渡日"].str[:17] = pd.to_datetime(df["約定日時受渡日"].str[:17], format="%y/%m/%d %H:%M:%S")
  df["execution_datetime"] = pd.to_datetime(df["約定日時受渡日"].str[:17], format="%y/%m/%d %H:%M:%S")
  # df["receipt date"] = df["約定日時受渡日"].str[17:].str.strip()
  df["profit"] = df["決済損益取引手数料"].str.replace(",","").astype(pd.Int64Dtype())
  df["swap"] = df["累計スワップ"].str.replace(",","").astype(pd.Int64Dtype())
  # df["expiration date"] = df["注文日時有効期限"].str[17:].str.strip()
  # df["change and cancel"] = df["変更取消"]
  df = df.drop(columns=columns_jp)
  return df

def add_data(*args):
  df = pd.concat(args)
  df = df.drop_duplicates(subset=["order_number"])
  df = df.sort_values(by="order_number", ascending=True)
  return df
