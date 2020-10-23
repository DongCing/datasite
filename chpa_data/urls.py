from django.urls import path
from chpa_data import views

app_name = 'chpa_data'
urlpatterns = [
  path('index/', views.index, name='index'),
  path(r'query', views.query, name='query'),

  # path(r'search/<str:column>/<str:kw>', views.search, name='search'),
]
