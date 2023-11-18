from django.contrib import admin
from .models import HistoryTable, ChartTable, HistoryLinkTable, ReviewTable, PositionTable

admin.site.register(HistoryTable)
admin.site.register(ChartTable)
admin.site.register(HistoryLinkTable)
admin.site.register(ReviewTable)
admin.site.register(PositionTable)
