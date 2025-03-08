from rest_framework import generics, status
from rest_framework.response import Response
from .models import ScrapeTask
from .serializers import ScrapeTaskSerializer
from .tasks import async_scrape

class ScrapeTaskCreateView(generics.CreateAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        async_scrape.delay(instance.id)

class ScrapeTaskDetailView(generics.RetrieveAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer

class ScrapeTaskListView(generics.ListAPIView):
    queryset = ScrapeTask.objects.all().order_by('-created_at')
    serializer_class = ScrapeTaskSerializer
    filterset_fields = ['status', 'url']
    search_fields = ['url', 'selector']