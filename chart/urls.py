from django.urls import path
# from .views import history, chart_detail ,chart_index, histories2edit, chart_add, chart_update, chart_delete, chart_image, none2edit, chart_image_day, diary, calendar_index, diary_create, diary_update, diary_delete, chart_image_review, review, review_later, review_index, review_update, review_create, review_delete, speed_order, market_settlement, position_update
from . import views

app_name = 'chart'

urlpatterns = [
    path('history/',views.history, name='history'),
    path('index/',views.chart_index, name='chart_index'),
    path('generate/',views.histories2edit, name='chart_generate'),
    path('create/',views.none2edit, name='chart_create'),
    path('add/',views.chart_add, name='chart_add'),
    path('update/<int:id>',views.chart_update, name='chart_update'),
    path('delete/<int:id>',views.chart_delete, name='chart_delete'),
    path('detail/<int:id>',views.chart_detail, name='chart_detail'),
    path('image/<int:id>',views.chart_image, name='chart_image'),
    path('review/image/<int:id>',views.chart_image_review, name='chart_image_review'),
    path('review/',views.review_index, name='review_index'),
    path('review/<int:id>',views.review, name='review'),
    path('review/<int:id>/later/<str:delta>',views.review_later, name='review_later'),
    path('review/update/<int:id>',views.review_update, name='review_update'),
    path('review/create/',views.review_create, name='review_create'),
    path('review/delete/<int:id>',views.review_delete, name='review_delete'),
    path('review/<int:id>/position/',views.speed_order, name='speed_order'),  # ReviewTableのid
    path('review/position/<int:id>',views.market_settlement, name='market_settlement'),  # PositionTableのid
    path('review/position/<int:id>/update/',views.position_update, name='position_update'),  # PositionTableのid
]
