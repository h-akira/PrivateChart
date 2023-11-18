# 基本
import sys
import os
import pandas as pd
import datetime
from pytz import timezone
# django
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q
from django.db.models import Sum
from django.conf import settings
# modelsとforms
from .models import HistoryTable, ChartTable, HistoryLinkTable, ReviewTable, PositionTable
from .forms import ChartForm, ReviewForm, ReviewUpdateForm, PositionSpeedForm, PositionMarketForm, PositionUpdateForm
# 独自関数
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import lib.chart
import lib.chart_settings
# チャート出力用
import io
import base64
from matplotlib import use
use("Agg")
import mplfinance as mpf

import pandas_datareader.data as web
import yfinance as yf
yf.pdr_override()

# 曜日変換要
WEEK = ("月","火","水","木","金","土","日")

# html用
history_header = [
  "アカウント",
  "注文番号",
  "取引種類",
  "通貨ペア",
  "売買",
  "注文タイプ",
  "取引数量",
  "状態",
  "失効理由",
  "注文日時",
  "注文レート",
  "執行条件",
  "約定日時",
  "約定レート",
  "決済損益",
  "スワップ",
]
history_width = [
  100,  # アカウント
  80,  # 注文番号
  100,  # 取引種類
  100,  # 通貨ペア
  50,  # 売買
  100,  # 注文タイプ
  80,  # 取引数量
  100,  # 状態
  80,  # 失効理由
  200,  # 注文日時
  100,  # 注文レート
  80,  # 執行条件
  200,  # 約定日時
  100,  # 約定レート
  100,  # 決済損益
  100  # スワップ
]

RATE_DIR = os.path.join(os.path.dirname(__file__), "../data/rate") 

@login_required
def history(request):
  histories_all = HistoryTable.objects.filter(user=request.user).order_by("-order_number","-order_datetime")
  per_page = request.GET.get('per_page', 50)
  paginator = Paginator(histories_all, per_page)
  page = request.GET.get('page')
  histories = paginator.get_page(page)
  context = {
    "histories":histories, 
    "header":history_header, 
    "width":history_width,
    "box":True, 
    "checked":False
  }
  return render(request, 'chart/history.html', context)

@login_required
def chart_index(request):
  _charts = ChartTable.objects.filter(user=request.user).order_by("-id")
  links = [HistoryLinkTable.objects.filter(chart=i).count() for i in _charts]
  header = [
    "登録名",
    "通貨ペア",
    "足",
    "基準日時",
    "新規+決済",
    "操作"
  ]
  width = [
  200,  # 登録名
  100,  # 通貨ペア
  50,  # 足
  200,  # 基準日時
  100,  # 新規+決済
  100  # 操作
  ]
  context = {"charts":_charts, "links":links, "header":header, "width":width, "box":False, "checked":False}
  return render(request, 'chart/chart_index.html', context)

@login_required
def chart_image(request,id, _HttpResponse=True, _chart=None, histories=None):
  # 該当のchartのデータを取得
  if _chart == None:
    _chart = get_object_or_404(ChartTable, pk=id)
  # 該当のチャートと紐付けられている取引履歴を取得
  if histories == None:
    histories = [i.history for i in HistoryLinkTable.objects.filter(chart=_chart)]
    histories = sorted(histories, reverse=True, key=lambda x: x.id)
    histories = sorted(histories, reverse=True, key=lambda x: x.order_datetime)
  # 為替データを取得
  # daysは要調整
  if "H" in _chart.rule:
    days = 60
  elif "D" in _chart.rule:
    days = 240
  elif _chart.rule[-1] == "T":
    minutes = int(_chart.rule[:-1])
    if minutes <= 3:
      days = 4
    elif minutes <= 15:
      days = 7
    else:
      days = 10
  else:
    print("Warning: chart_image: rule may not be valid")
    days = 10
  start_date = (_chart.standard_datetime-datetime.timedelta(days=days)).date()
  end_date = (_chart.standard_datetime+datetime.timedelta(days=days)).date()
  df = lib.chart.GMO_dir2DataFrame(
    os.path.join(os.path.dirname(__file__), "../data/rate"), 
    pair=_chart.pair,
    date_range=[
      start_date,end_date
    ],
    guarantee=True
  ) 
  if df is None:
    yf = True
  else:
    yf = False
    # 足を変換
    df = lib.chart.resample(df, _chart.rule)
    if len(df)<_chart.plus_delta+_chart.minus_delta+60:  # 要調整
      yf = True
  if yf:
    interval = _chart.rule.replace("T", "m").replace("H", "h").replace("D", "d")
    if interval not in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d"]:
      resample = True
      interval = str(1)+interval[-1]
    else:
      resample = False
    if "^" in _chart.pair:
      ticker = _chart.pair
    else:
      ticker = f'{_chart.pair.replace("/","")}=X'
    # daysは要調整
    if interval == "1m":
      days = 3
    elif interval == "2m":
      days = 5
    elif interval == "5m":
      days = 10
    elif interval in ["15m", "30m"]:
      days = 25
    elif interval in ["60m", "90m", "1h"]:
      days = 50
    else:
      days = 240
    start_datetime = _chart.standard_datetime-datetime.timedelta(days=days)
    end_datetime = _chart.standard_datetime+datetime.timedelta(days=days)
    end_datetime = min(end_datetime, datetime.datetime.now(timezone(settings.TIME_ZONE))-datetime.timedelta(minutes=1))
    df = web.get_data_yahoo(tickers=ticker,start=start_datetime, end=end_datetime, interval=interval)
    if df.index[0].tzinfo is None:
      df.index = df.index.tz_localize('UTC')
    df.index = df.index.tz_convert('Asia/Tokyo')
    if resample:
      df = chart.chart.resample(df, _chart.rule)

  if yf:
    print("get data from yahoo finance")
  else:
    print("get data from GMO")
  # テクニカル指標を追加
  df = lib.chart_settings.add_technical_columns(df)
  # 最もstandard_datetimeに近い列の周辺のデータを取得する
  target_datetime = pd.Timestamp(_chart.standard_datetime)
  # nearest_index = (pd.DataFrame(df.index) - target_datetime).abs().idxmin().date
  nearest_index = (pd.DataFrame(df.index) - target_datetime).abs().idxmin().Datetime
  start_index = max(0, nearest_index - _chart.minus_delta)
  end_index = min(nearest_index + _chart.plus_delta, len(df) - 1)
  df = df.iloc[start_index:end_index+1]
  
  ### チャートを作成
  # 共通部分
  plot_args = lib.chart_settings.plot_args.copy()
  # テクニカル指標を追加
  plot_args =  lib.chart_settings.add_technical_lines(plot_args, df)
  # 横線
  hlines=dict(hlines=[],colors=[],linewidths=[])
  for history in histories:
    if history.order_rate != None:
      hlines["hlines"].append(history.order_rate)
      if history.state == "canceled":
        hlines["colors"].append("#7d7d7d")
      elif history.buy_sell == "buy":
        hlines["colors"].append("r")
      else:
        hlines["colors"].append("b")
      hlines["linewidths"].append(0.1)
  plot_args["hlines"] = hlines
  # 取引期間
  # execution = [i.execution_datetime for i in histories if i.execution_datetime != None]
  # if len(execution) >= 2:
  #   transaction_start=pd.Timestamp(min(execution).astimezone(timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M"),tz=timezone("Asia/Tokyo"))
  #   transaction_end=pd.Timestamp(max(execution).astimezone(timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M"),tz=timezone("Asia/Tokyo"))
  #   dates_df = pd.DataFrame(df.index)
  #   where_values = pd.notnull(dates_df[(dates_df>=transaction_start)&(dates_df<=transaction_end)])['date'].values
  #   max_value = df["bb_up_3"].max(),
  #   min_value = df["bb_down_3"].min(),
  #   plot_args["fill_between"] = dict(y1=max_value, y2=min_value, where=where_values, alpha=0.3) 
  # 縦線
  vlines=dict(vlines=[],colors=[],linewidths=[])
  for history in histories:
    if history.execution_datetime != None and history.state != "canceled" and history.order_rate != None:
      vlines["vlines"].append(history.execution_datetime)
      if history.buy_sell == "buy":
        vlines["colors"].append("r")
      else:
        vlines["colors"].append("b")
      vlines["linewidths"].append(0.1)
  plot_args["vlines"] = vlines
  # 画像の大きさ
  plot_args["figsize"] = (14,8)
  # plot_args["figratio"] = (10,6)
  # 画像の出力先
  buf = io.BytesIO()
  plot_args["savefig"] = {'fname':buf,'dpi':100}
  # 出力
  mpf.plot(df, **plot_args)
  buf.seek(0)
  if _HttpResponse:
    return HttpResponse(buf, content_type='image/png')
  else:
    image_data = base64.b64encode(buf.getvalue()).decode("utf-8")
    return image_data
    # htmldjangoにおいて以下のように記述することで出力できる:
    # <img src="data:image/png;base64,{{ image_data  }}" alt="Chart">

@login_required
def chart_detail(request, id):
  # 該当のchartのデータを取得
  _chart = get_object_or_404(ChartTable, pk=id)
  form = ChartForm(instance=_chart)
  # 該当のチャートと紐付けられている取引履歴を取得
  histories = [i.history for i in HistoryLinkTable.objects.filter(chart=_chart)]
  histories = sorted(histories, reverse=True, key=lambda x: x.id)
  histories = sorted(histories, reverse=True, key=lambda x: x.order_datetime)
  image_data = chart_image(request, id, _HttpResponse=False, _chart=_chart, histories=histories)
  ### 渡すもの
  context = {
    "id": id,
    "chart":_chart,
    "histories":histories, 
    "image_data":image_data,
    "form":form,
    "header":history_header, 
    "width":history_width,
    "box":False, 
    "checked":False,
  }
  return render(request, 'chart/chart_detail.html', context)

@login_required
def histories2edit(request):
  histories = HistoryTable.objects.filter(
    id__in=request.POST.getlist("register")).order_by("-order_number","-order_datetime"
  )
  dts = [i[0].timestamp() for i in histories.values_list("execution_datetime") if i[0] != None]
  if len(dts) == 0:
    dts = [i[0].timestamp() for i in histories.values_list("order_datetime") if i[0] != None]
  timezones = [i[0].tzinfo for i in histories.values_list("execution_datetime") if i[0] != None]
  if len(timezones) != timezones.count(timezones[0]):
    raise Exception
  pairs = [i[0] for i in histories.values_list("pair")]
  if len(pairs) != pairs.count(pairs[0]):
    raise Exception
  ave = datetime.datetime.fromtimestamp(sum(dts)/len(dts),tz=timezones[0])
  initial = {
    # "user":request.user,
    "pair":pairs[0],
    "standard_datetime": ave,
    "plus_delta":100,
    "minus_delta":100
  }
  form = ChartForm(initial=initial)
  context = {
    "histories":histories,
    "header":history_header,
    "width":history_width,
    "form":form,
    "table":True,
    "box":True, 
    "checked":True,
  }
  return render(request, 'chart/edit.html', context)

@login_required
def none2edit(request):
  initial = {
    "plus_delta":100,
    "minus_delta":100
  }
  form = ChartForm(initial=initial)
  context = {
    "form":form,
    "table":False,
  }
  return render(request, 'chart/edit.html', context)

@login_required
def chart_add(request):
  form = ChartForm(request.POST)
  histories = HistoryTable.objects.filter(id__in=request.POST.getlist("register"))
  if form.is_valid():
    instance = form.save(commit=False)  # まだDBには保存しない
    instance.user = request.user  # ログインしているユーザー情報をセット
    instance.save()  # DBに保存
    if histories.exists():
      for history in histories:
        obj = HistoryLinkTable(chart=instance, history=history)
        obj.save()
    return redirect("chart:chart_detail", instance.id)
  else:
    print("not valid")
    return redirect("chart:history")

@login_required
def chart_update(request,id):
  _chart = get_object_or_404(ChartTable, pk=id)
  form = ChartForm(request.POST, instance=_chart)
  if form.is_valid():
    form.save()
    return redirect("chart:chart_detail",id)
  else:
    return redirect("chart:chart_detail",id)

@login_required
def chart_delete(request, id):
  _chart = get_object_or_404(ChartTable, pk=id)
  _chart.delete()
  return redirect("chart:chart_index")

@login_required
def review(request, id):
  _review = get_object_or_404(ReviewTable, pk=id)
  image, close_bid, close_ask, increase_rate = chart_image_review(
    request,
    id,
    _HttpResponse=False,
    _review=_review
  )
  review_form = ReviewUpdateForm(instance=_review)
  dt = _review.dt.astimezone(timezone("Asia/Tokyo"))
  position_speed_form = PositionSpeedForm(
    initial = {
      "position_datetime" :dt,
      "pair" : _review.pair
    }
  )
  positions = PositionTable.objects.filter(review=_review)
  open_positions = positions.filter(
    Q(settlement_datetime__gt=_review.dt) | Q(settlement_datetime=None),
  ).order_by("id")
  close_positions = positions.filter(
    settlement_datetime__lte=_review.dt
  ).order_by("-settlement_datetime")
  evaluations = []
  market_forms = []
  position_update_forms = []
  for position in open_positions:
    if position.buy_sell == "buy":
      settlement_bid_ask = "BID"  # 決済のときだから逆
    elif position.buy_sell == "sell":
      settlement_bid_ask = "ASK"  # 決済のときだから逆
    else:
      raise Exception
    rate = lib.chart.get_rate(
      dir_name = RATE_DIR,
      pair = position.pair,
      dt = dt,
      BID_ASK = settlement_bid_ask
    )
    profit = get_profit(
      pair = position.pair, 
      buy_sell = position.buy_sell, 
      quantity = position.quantity, 
      position_rate = position.position_rate, 
      settlement_datetime = dt,
      settlement_rate = rate
    )
    if position.limit != None:
      limit_profit = get_profit(
        pair = position.pair, 
        buy_sell = position.buy_sell, 
        quantity = position.quantity, 
        position_rate = position.position_rate, 
        settlement_datetime = dt,
        settlement_rate = position.limit
      )
    else:
      limit_profit = None
    # 指値，逆指値の損益を計算する
    # クロス円ではない場合は決済日時ではなく現在日時で円に換算するのでここ
    if position.stop != None:
      stop_profit = get_profit(
        pair = position.pair, 
        buy_sell = position.buy_sell, 
        quantity = position.quantity, 
        position_rate = position.position_rate, 
        settlement_datetime = dt,
        settlement_rate = position.stop
      )
    else:
      stop_profit = None
    evaluations.append(
      {
        "rate":rate,
        "profit":profit,
        "limit_profit":limit_profit,
        "stop_profit":stop_profit
      }
    )
    market_forms.append(
      PositionMarketForm(
        initial={
          "settlement_datetime":dt,
          "settlement_rate":rate,
          "profit":profit
        }
      )
    )
  # 指値・逆指値の更新用
    position_update_forms.append(
      PositionUpdateForm(
        instance=position,
        initial={
          "now_datetime":dt,
          "now_rate":rate
        }
      )
    )
  # open_positions = list(open_positions.values())
  evaluation_profit_all = sum([e["profit"] for e in evaluations])
  settlement_profit_all = close_positions.aggregate(Sum("profit"))["profit__sum"]
  if settlement_profit_all == None:
    settlement_profit_all = 0
  context = {
    "review":_review,
    "year":dt.year, 
    "month":dt.month,
    "day":dt.day,
    "weekday":WEEK[dt.weekday()],
    "time_text": dt.strftime('%H時%M分'),
    "id":id,
    "image" : image,
    "close_bid":close_bid,
    "close_ask":close_ask,
    "increase_rate" : increase_rate,
    "review_form":review_form,
    "position_speed_form":position_speed_form,
    "open_positions_zip":zip(open_positions, evaluations, market_forms, position_update_forms),
    "close_positions":close_positions,
    "evaluations":evaluations,
    "evaluation_profit_all": evaluation_profit_all,
    "settlement_profit_all": settlement_profit_all
  }
  return render(request, 'chart/review.html', context)

@login_required
def review_later(request, id, delta):
  delta = int(delta)
  obj = ReviewTable.objects.get(pk=id) 
  obj.dt = obj.dt + datetime.timedelta(minutes=delta)
  obj.save()
  return redirect("chart:review",id)


@login_required
def chart_image_review(request, id, _HttpResponse=True, _review=None, BID_ASK="BID"):
  if _review == None:
    _review = get_object_or_404(ReviewTable, pk=id)
  # 為替データを取得
  if "H" in _review.rule:
    days = 50
  elif "D" in _review.rule:
    days = 250
  else:
    days = 10
  for bid_ask  in ["BID","ASK"]:
    _df = lib.chart.GMO_dir2DataFrame(
      os.path.join(os.path.dirname(__file__), "../data/rate"), 
      pair=_review.pair,
      date_range=[
        (_review.dt-datetime.timedelta(days=days)).date(),
        (_review.dt+datetime.timedelta(days=2)).date(),
      ],
      BID_ASK = bid_ask
    )
    ## 00秒時点なので，1分前のCloseまで
    _df = _df[_df.index <= _review.dt.astimezone(timezone('Asia/Tokyo')) - datetime.timedelta(minutes=1)]
    if bid_ask == "BID":
      df_BID = _df.copy()
      if BID_ASK == "BID":
        df = _df.copy()
    else:
      df_ASK = _df.copy()
      if BID_ASK == "ASK":
        df = _df.copy()
  # 始値（00秒の時点を返す）
  close_bid = df_BID["Close"].iloc[-1]
  close_bid_before = df_BID["Close"].iloc[-2]
  close_ask = df_ASK["Open"].iloc[-1]
  close_ask_before = df_ASK["Open"].iloc[-2]
  if BID_ASK == "BID":
    increase_rate = close_bid - close_bid_before
    close = close_bid
  elif BID_ASK == "ASK":
    increase_rate = close_ask - close_ask_before
    close = close_ask
  else:
    raise ValueError
  # 足
  df = lib.chart.resample(df, _review.rule)
  # テクニカル指標を追加
  df = lib.chart_settings.add_technical_columns(df)
  # 抽出
  df = df.iloc[-_review.delta:]
  ### チャートを作成
  # 共通部分
  plot_args = lib.chart_settings.plot_args.copy()
  # 横線
  positions = PositionTable.objects.filter(review=_review)
  open_positions = positions.filter(
    Q(settlement_datetime__gt=_review.dt) | Q(settlement_datetime=None),
  ).order_by("id")
  # hlines=dict(hlines=[close],colors=["#ff7f50"],linewidths=[0.1], linestyle=["-"])
  hlines=dict(hlines=[close],colors=["b"],linewidths=[0.1], linestyle=["-"])
  plot_args["hlines"] = hlines
  # 保有ポジションの注文レート
  # linewidthsを設定した状態で破線を同時に引けないようなのでaddplot
  position_lines = []
  # ボリンジャーバンドの範囲内+少々の線のみ表示する
  bb_max = df["bb_up_3"].max()
  bb_min = df["bb_down_3"].min()
  bb_delta = bb_max-bb_min
  bb_max += bb_delta * 0.1
  bb_min -= bb_delta * 0.1
  for position in open_positions:
    if _review.pair == position.pair:
      if bb_min <= position.position_rate <= bb_max:
        if position.buy_sell == "buy":
          position_lines.append(
            mpf.make_addplot([position.position_rate]*len(df), panel=0, color='r', linestyle='--', linewidths=0.1)
          )
        elif position.buy_sell == "sell":
          position_lines.append(
            mpf.make_addplot([position.position_rate]*len(df), panel=0, color='b', linestyle='--', linewidths=0.1)
          )
      if position.limit:
        if bb_min <= position.limit <= bb_max:
          position_lines.append(
            mpf.make_addplot([position.limit]*len(df), panel=0, color='#ff00ff', linestyle='-', linewidths=0.1)
          )
      if position.stop:
        if bb_min <= position.stop <= bb_max:
          position_lines.append(
            mpf.make_addplot([position.stop]*len(df), panel=0, color='#ff00ff', linestyle='-', linewidths=0.1)
          )
  plot_args["addplot"] = position_lines
  # テクニカル指標を追加
  plot_args =  lib.chart_settings.add_technical_lines(plot_args, df)
  # 画像の大きさ
  plot_args["figsize"] = (13,9)
  # 画像の出力先
  buf = io.BytesIO()
  plot_args["savefig"] = {'fname':buf,'dpi':100}
  # タイトル
  # plot_args["title"] = f"{pair} 15T"
  # 出力
  mpf.plot(df, **plot_args)
  buf.seek(0)
  if _HttpResponse:
    return HttpResponse(buf, content_type='image/png')
  else:
    image_data = base64.b64encode(buf.getvalue()).decode("utf-8")
    return image_data, close_bid, close_ask, increase_rate
    # htmldjangoにおいて以下のように記述することで出力できる:
    # <img src="data:image/png;base64,{{ image_data  }}" alt="Chart">

@login_required
def review_index(request):
  _review = ReviewTable.objects.filter(user=request.user).order_by("-id")
  context = {
    "reviews": _review
  }
  return render(request, 'chart/review_index.html', context)

@login_required
def review_update(request,id):
  _review = get_object_or_404(ReviewTable, pk=id)
  form = ReviewUpdateForm(request.POST, instance=_review)
  if form.is_valid():
    form.save()
    return redirect("chart:review",id)
  else:
    print(form.errors)
    print(request.POST)
    return redirect("chart:review",id)

@login_required
def review_create(request):
  if request.method == 'POST':
    form = ReviewForm(request.POST)
    if form.is_valid():
      instance = form.save(commit=False)  # まだDBには保存しない
      instance.user = request.user  # ログインしているユーザー情報をセット
      instance.save()  # DBに保存
      return redirect("chart:review", instance.id)
    else:
      print("not valid")
      return redirect("chart:review_index")
  else:
    form = ReviewForm()
    context = {
    "form":form,
    }
    return render(request, 'chart/review_create.html', context)

@login_required
def review_delete(request, id):
  _review = get_object_or_404(ReviewTable, pk=id)
  _review.delete()
  return redirect("chart:review_index")

@login_required
def speed_order(request, id):
  if request.method == 'POST':
    _review = get_object_or_404(ReviewTable, pk=id)
    form = PositionSpeedForm(request.POST)
    if form.is_valid():
      instance = form.save(commit=False)  # まだDBには保存しない
      instance.review = _review
      button_type = request.POST.get('button_type')
      if button_type == 'buy':
        instance.buy_sell = "buy"
        BID_ASK = "ASK"
      elif button_type == 'sell':
        instance.buy_sell = "sell"
        BID_ASK = "BID"
      position_rate = lib.chart.get_rate(
        os.path.join(os.path.dirname(__file__),"../data/rate"),
        pair=instance.pair,
        dt=instance.position_datetime,
        BID_ASK = BID_ASK
      )
      instance.position_rate = position_rate
      # 指値，逆指値の処理
      instance.condition, instance.settlement_datetime, instance.settlement_rate = limit_stop(
        pair=instance.pair,
        buy_sell = instance.buy_sell,
        now_datetime = instance.position_datetime,
        limit = instance.limit,
        stop = instance.stop,
        now_rate = instance.position_rate
      )
      # 利益の計算
      if instance.settlement_datetime != None:
        instance.profit = get_profit(
          pair = instance.pair, 
          buy_sell = instance.buy_sell, 
          quantity = instance.quantity, 
          position_rate = instance.position_rate, 
          settlement_datetime = instance.settlement_datetime, 
          settlement_rate = instance.settlement_rate
        )
      instance.save()  # DBに保存
      return redirect("chart:review", id)
    else:
      print("not valid")
      return redirect("chart:review_index")

@login_required
def market_settlement(request,id):
  _position = get_object_or_404(PositionTable, pk=id)
  form = PositionMarketForm(request.POST, instance=_position)
  if form.is_valid():
    form.save()
    return redirect("chart:review",_position.review.id)

@login_required
def position_update(request,id):
  _position = get_object_or_404(PositionTable, pk=id)
  if request.method == 'POST':
    form = PositionUpdateForm(request.POST, instance=_position)
    if form.is_valid():
      # 指値，逆指値の処理
      form.instance.condition, form.instance.settlement_datetime, form.instance.settlement_rate = limit_stop(
        pair=_position.pair,
        buy_sell = _position.buy_sell,
        now_datetime = form.cleaned_data.get('now_datetime', None),  # Noneはたぶんいらない
        limit = form.instance.limit,
        stop = form.instance.stop,
        now_rate = form.cleaned_data.get('now_rate', None),  # Noneはたぶんいらない
      )
      # 利益の計算
      if form.instance.settlement_datetime != None:
        form.instance.profit = get_profit(
          pair = _position.pair, 
          buy_sell = _position.buy_sell, 
          quantity = _position.quantity, 
          position_rate = _position.position_rate, 
          settlement_datetime = form.instance.settlement_datetime, 
          settlement_rate = form.instance.settlement_rate
        )
      form.save()
      return redirect("chart:review",_position.review.id)

###############################################################
# 以下は内部処理用
###############################################################
def limit_stop(pair, buy_sell, now_datetime, limit=None, stop=None, deadline=14, dir_name=RATE_DIR, now_rate=None):
  # deadlineは有効期限で単位は日
  # now_rateは指値，逆指値の値の範囲に問題がないか確認するために用いる
  if limit == None and stop== None:
    return None, None, None
  # 値に問題ないか確認
  if now_rate != None:
    if limit != None:
      if buy_sell == "buy" and now_rate >= limit:
        raise ValueError
      elif buy_sell == "sell" and now_rate <= limit:
        raise ValueError
    if stop != None:
      if buy_sell == "buy" and now_rate <= stop:
        raise ValueError
      elif buy_sell == "sell" and now_rate >= stop:
        raise ValueError
  # データ取得
  df = lib.chart.GMO_dir2DataFrame(
    dir_name = dir_name, 
    pair=pair,
    date_range=[
      (now_datetime-datetime.timedelta(hours=6)).date(),
      (now_datetime+datetime.timedelta(days=deadline+1)).date()
    ]
  ) 
  # 01秒から60秒の範囲を調べた上で決済は60秒，すなわち1分後なので最後にshift
  df = df[df.index > now_datetime.astimezone(timezone('Asia/Tokyo')) - datetime.timedelta(minutes=1)]
  df = df.shift(1)
  df.dropna(inplace=True)
  if stop:
    if buy_sell == "buy":
      stop_datetime = df[df['Low'] <= stop].index.min()
    elif buy_sell == "sell":
      stop_datetime = df[df['High'] >= stop].index.min()
    else:
      raise Exception
  if limit:
    if buy_sell == "buy":
      limit_datetime = df[df['High'] >= limit].index.min()
    elif buy_sell == "sell":
      limit_datetime = df[df['Low'] <= limit].index.min()
    else:
      raise Exception
  if (limit == None or pd.isna(limit_datetime)) and (stop == None or pd.isna(stop_datetime)):
    return None, None, None
  elif limit == None or pd.isna(limit_datetime):
    return "stop", stop_datetime, stop
  elif stop == None or pd.isna(stop_datetime):
    return "limit", limit_datetime, limit
  elif limit_datetime < stop_datetime:
    return "limit", limit_datetime, limit
  else:
    # 損切り優先
    return "stop", stop_datetime, stop
  
def get_profit(pair, buy_sell, quantity, position_rate, settlement_datetime, settlement_rate=None, dir_name=RATE_DIR):
  # settlement_datetimeはsettlement_rateが指定されている場合にはクロス円以外の場合の円への換算のみに使用
  # buy_sellは新規のときの売買
  if buy_sell == "buy":
    settlement_bid_ask = "BID"
  elif buy_sell == "sell":
    settlement_bid_ask = "ASK"
  else:
    raise Exception
  if settlement_rate == None:  # 未使用
    settlement_rate = lib.chart.get_rate(
      dir_name = dir_name, 
      pair = pair,
      dt = settlement_datetime,
      BID_ASK = settlement_bid_ask
    )
  if pair[-3:] == "JPY":  # クロス円，1単位10000通貨
    if buy_sell == "buy":
      profit = round((settlement_rate - position_rate) * quantity * 10000)
    elif buy_sell == "sell":
      profit = -round((settlement_rate - position_rate) * quantity * 10000)
    else:
      raise Exception
  else:  # それ以外，1単位1通貨
    # クロス通貨で利益を計算
    if buy_sell == "buy":
      profit = (settlement_rate - position_rate) * quantity * 10000
    elif buy_sell == "sell":
      profit = -((settlement_rate - position_rate) * quantity) * 10000
    else:
      raise Exception
    # 円にする
    to_yen_pair = f"{pair[-3:]}/JPY"
    to_yen_rate = lib.chart.get_rate(
      dir_name = dir_name, 
      pair = to_yen_pair,
      dt = settlement_datetime,
      BID_ASK = "BID"
    )
    profit = round(profit * to_yen_rate)
  return profit

