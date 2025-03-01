from django.urls import path
from .views import ScrapeTaskCreateView, ScrapeTaskDetailView, ScrapeTaskListView

urlpatterns = [
    path('scrape/', ScrapeTaskCreateView.as_view(), name='scrape-create'),
    path('scrape/<int:pk>/', ScrapeTaskDetailView.as_view(), name='scrape-detail'),
    path('scrape/list/', ScrapeTaskListView.as_view(), name='scrape-list'),
]
