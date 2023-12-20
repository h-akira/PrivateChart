from django.db import models
from django.contrib.auth.models import User
# from django.utils import timezone

KIND = (("new","新規"),("settlement","決済"))
BUY_SELL = (("buy","買"),("sell","売"))
STATE = (("accepted","受付済"),("executed","約定済"),("canceled","取消済"))
CONDITION = (("limit","指値"),("stop","逆指値"),("market","成行"))
RULE = (
  ("1T","1分足"),
  ("3T","3分足"),
  ("5T","5分足"),
  ("10T","10分足"),
  ("15T","15分足"),
  ("30T","30分足"),
  ("1H","1時間足"),
  ("4H","4時間足"),
  ("D","日足"),
)
PAIR = (
  ("USD/JPY", "USD/JPY"),
  ("EUR/JPY","EUR/JPY"),
  ("EUR/USD","EUR/USD"),
  ("GBP/JPY","GBP/JPY"),
  ("AUD/JPY","AUD/JPY")
)
COLOR = (
  ("#FF0000","赤"),
  ("#FFA500","オレンジ"),
  ("#FFFF00","黄"),
  ("#00FF00","緑"),
  ("#00FFFF","水色"),
  ("#0000FF","青"),
  ("#800080","紫"),
)

class TagTable(models.Model):
  user = models.ForeignKey(User,on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  memo = models.TextField()
  color = models.CharField(max_length=31,null=True, blank=True, choices=COLOR)
  def __str__(self):
    return self.name

class HistoryTable(models.Model):
  user = models.ForeignKey(User,on_delete=models.CASCADE)
  account = models.CharField(max_length=50)
  order_number = models.IntegerField()
  pair = models.CharField(max_length=10)  # choicesは利用しない
  order_type  = models.CharField(max_length=20)
  kind = models.CharField(max_length=10, choices=KIND)
  buy_sell = models.CharField(max_length=10, choices=BUY_SELL)
  quantity = models.FloatField()
  state = models.CharField(max_length=10, choices=STATE)
  revocation_reason = models.CharField(max_length=10, null=True, blank=True)  # 失効理由(ほぼOCO)
  order_datetime = models.DateTimeField()
  order_rate = models.FloatField(null=True, blank=True)
  condition = models.CharField(max_length=10, choices=CONDITION)
  execution_datetime = models.DateTimeField(null=True, blank=True)
  execution_rate = models.FloatField(null=True, blank=True)
  unit = models.CharField(max_length=10,default="JPY")
  profit = models.FloatField(null=True, blank=True)
  swap = models.FloatField(null=True, blank=True)
  memo = models.CharField(max_length=511)
  class Meta:
    constraints = [
      models.UniqueConstraint(
        fields=["user", "account", "order_number"],
        name="history_unique"
      )
    ]
  
def default_chart_name():
    last_review = ReviewTable.objects.last()
    next_id = last_review.id + 1 if last_review else 1
    return f"チャート（{next_id}）"

class ChartTable(models.Model):
  user = models.ForeignKey(User,on_delete=models.CASCADE)
  # name = models.CharField(max_length=255, default=timezone.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
  name = models.CharField(max_length=255, default=default_chart_name)
  # pair = models.CharField(max_length=10, choices=PAIR)
  pair = models.CharField(max_length=10)
  rule = models.CharField(max_length=10, choices=RULE)
  standard_datetime = models.DateTimeField()
  minus_delta = models.IntegerField(default=100)
  tags = models.ManyToManyField(TagTable, related_name="chart_tags")
  plus_delta = models.IntegerField(default=100)
  memo = models.TextField(null=True, blank=True)
  def __str__(self):
    return self.name

class HistoryLinkTable(models.Model):
  chart = models.ForeignKey(ChartTable, on_delete=models.CASCADE)
  history = models.ForeignKey(HistoryTable, on_delete=models.CASCADE)

def default_review_name():
    last_review = ReviewTable.objects.last()
    next_id = last_review.id + 1 if last_review else 1
    return f"レビュー（{next_id}）"

class ReviewTable(models.Model):
  user = models.ForeignKey(User,on_delete=models.CASCADE)
  # name = models.CharField(max_length=255, default=timezone.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
  name = models.CharField(max_length=255, default=default_review_name)
  pair = models.CharField(default="USD/JPY", max_length=10, choices=PAIR)
  rule = models.CharField(default="15T", max_length=10, choices=RULE)
  delta = models.IntegerField(default=150)
  dt = models.DateTimeField()
  memo = models.CharField(max_length=511,null=True, blank=True)

class PositionTable(models.Model):
  review = models.ForeignKey(ReviewTable, on_delete=models.CASCADE)
  pair = models.CharField(max_length=10, choices=PAIR)
  quantity = models.FloatField()
  buy_sell = models.CharField(max_length=10, choices=BUY_SELL)
  position_datetime = models.DateTimeField()
  position_rate = models.FloatField()
  condition = models.CharField(max_length=10, choices=CONDITION, null=True, blank=True)
  limit = models.FloatField(null=True, blank=True)
  stop = models.FloatField(null=True, blank=True)
  profit = models.IntegerField(null=True, blank=True)
  settlement_datetime = models.DateTimeField(null=True, blank=True)
  settlement_rate = models.FloatField(null=True, blank=True)

