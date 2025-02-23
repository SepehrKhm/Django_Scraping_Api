from rest_framework import generics
from .models import ScrapeTask
from .serializers import ScrapeTaskSerializer
from .tasks import async_scrape

class ScrapeTaskCreateView(generics.CreateAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        async_scrape.delay(instance.id)