from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework_api_key.models import APIKey
from .models import ScrapeTask, JobLog, ScrapeAPIKey
from .serializers import ScrapeTaskSerializer, JobLogSerializer
from .tasks import sync_scrape

class HasAPIKeyOrQueryParam(HasAPIKey):
    def has_permission(self, request, view):
        api_key = request.query_params.get('api_key', '')
        if api_key:
            # Try both your API keys
            if api_key in ['4Q9MlNIl.7KDzGhN7OsH27xMK8ZcYw3pnyfeGzVR2', 'QKq23mW7.NCtTgRX8n6EpdSKZYEfqCKXrbv416s09']:
                request.META['HTTP_X_API_KEY'] = api_key
                return True
            print(f"Invalid API key: {api_key}")
            return False
        return super().has_permission(request, view)

class ScrapeTaskCreateView(generics.CreateAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKeyOrQueryParam]
    
    def get(self, request, *args, **kwargs):
        return Response({"message": "Ready to accept scraping tasks"})

    def perform_create(self, serializer):
        # Save without API key for now
        instance = serializer.save(api_key=None)
        sync_scrape.delay(instance.id)

class ScrapeTaskDetailView(generics.RetrieveAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKeyOrQueryParam]

    def get_queryset(self):
        api_key = self.request.query_params.get('api_key') or self.request.META.get("HTTP_X_API_KEY")
        return ScrapeTask.objects.all()  # For now, allow access to all tasks

class ScrapeTaskListView(generics.ListAPIView):
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKeyOrQueryParam]
    filterset_fields = ['status', 'url']
    search_fields = ['url', 'selector']

    def get_queryset(self):
        return ScrapeTask.objects.all().order_by('-created_at')

class ScrapeTaskProgressView(generics.RetrieveAPIView):
    queryset = ScrapeTask.objects.all()
    serializer_class = ScrapeTaskSerializer
    permission_classes = [HasAPIKeyOrQueryParam]

    def get(self, request, pk, *args, **kwargs):
        task = self.get_object()
        return Response({
            'id': task.id,
            'status': task.status,
            'progress': task.progress,
            'current_position': task.current_position,
            'total_items': task.total_items,
            'logs': list(task.logs.values('timestamp', 'level', 'message').order_by('-timestamp')[:5])
        })