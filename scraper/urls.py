from django.urls import path
from .views import ScrapeTaskCreateView

urlpatterns = [
    path('scrape/', ScrapeTaskCreateView.as_view()),
]