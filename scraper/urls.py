from django.urls import path
from .views import ScrapeTaskCreateView, ScrapeTaskDetailView, ScrapeTaskListView, ScrapeTaskProgressView

urlpatterns = [
    path('scrape/', ScrapeTaskCreateView.as_view(), name='scrape-create'),
    path('scrape/list/', ScrapeTaskListView.as_view(), name='scrape-list'),
    path('scrape/<int:pk>/', ScrapeTaskDetailView.as_view(), name='scrape-detail'),
    path('scrape/<int:pk>/progress/', ScrapeTaskProgressView.as_view(), name='scrape-progress'),
]