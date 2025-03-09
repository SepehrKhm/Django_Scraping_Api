from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from .models import ScrapeTask, JobLog
from .serializers import ScrapeTaskSerializer, JobLogSerializer
from .tasks import sync_scrape

class HasAPIKeyOrQueryParam(HasAPIKey):
    def has_permission(self, request, view):
        api_key = request.query_params.get('api_key')
        if api_key:
            request.META['HTTP_X_API_KEY'] = api_key
        return super().has_permission(request, view)

class ScrapeTaskCreateView(generics.CreateAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKey]

    def perform_create(self, serializer):
        api_key = self.request.META.get("HTTP_X_API_KEY")
        instance = serializer.save(api_key_id=api_key)
        sync_scrape.delay(instance.id)

class ScrapeTaskDetailView(generics.RetrieveAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        return ScrapeTask.objects.filter(
            api_key__key_id=self.request.META.get("HTTP_X_API_KEY")
        )

class ScrapeTaskListView(generics.ListAPIView):
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKeyOrQueryParam]
    filterset_fields = ['status', 'url']
    search_fields = ['url', 'selector']

    def get_queryset(self):
        return ScrapeTask.objects.filter(
            api_key__key_id=self.request.META.get("HTTP_X_API_KEY")
        ).order_by('-created_at')