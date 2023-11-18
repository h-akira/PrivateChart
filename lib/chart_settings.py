import sys
import os
import mplfinance as mpf
from . import chart

plot_args = {
  "type":"candle",
  # "style":"charles",
  "style":"starsandstripes",
  # "style":"blueskies",
}

def add_technical_columns(df):
  # ボリンジャーバンドを追加
  df = chart.add_BBands(df,20,2,0,name={"up":"bb_up_2", "middle":"bb_middle", "down":"bb_down_2"})
  df = chart.add_BBands(df,20,3,0,name={"up":"bb_up_3", "middle":"bb_middle", "down":"bb_down_3"})
  # 移動平均線を追加
  df = chart.add_SMA(df, 9, "SMA_9") 
  df = chart.add_SMA(df, 20, "SMA_20") 
  df = chart.add_SMA(df, 60, "SMA_60") 
  return df

def add_technical_lines(plot_args, df):
  # ボリンジャーバンドを追加
  # 線
  lines=[
    {
      "data":df[["bb_up_2","bb_down_2"]],
      "linestyle":"dashdot",
      "color":"#aa4c8f",
      "alpha":1
    },
    {
      "data":df[["bb_up_3","bb_down_3"]],
      "linestyle":"dashdot",
      "color":"#96514d",
      "alpha":1
    },
    {
      "data":df[["SMA_9"]],
      "color":"#bc763c",
      "alpha":1
    },
    {
      "data":df[["SMA_20"]],
      "color":"#3eb370",
      "alpha":1
    },
    {
      "data":df[["SMA_60"]],
      "color":"y",
      "alpha":1
    }
  ]
  if "addplot" in plot_args.keys():
    plot_args["addplot"] += [mpf.make_addplot(**line_args) for line_args in lines]
  else:
    plot_args["addplot"] = [mpf.make_addplot(**line_args) for line_args in lines]
  return plot_args


# 個別に設定が必要なもの
# - figsize 例: (19,8)
# - savefig 例: {'fname':buf,'dpi':100}
# - hlines 例: {'hlines':[136.28,136.32],'colors':['g','r'],'linewidths'=[1,1]}
# - vlines
# - fill_between
# など



