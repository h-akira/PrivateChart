from django.urls import path
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
    path('tag/index/',views.TagListView.as_view(), name='tag_index'),
    path('tag/create/',views.TagCreateView.as_view(), name='tag_create'),
    path('tag/update/<int:pk>',views.TagUpdateView.as_view(), name='tag_update'),
    path('tag/delete/<int:pk>',views.TagDeleteView.as_view(), name='tag_delete'),
]
