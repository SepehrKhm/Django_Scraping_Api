from rest_framework import serializers
from .models import ScrapeTask

class ScrapeTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeTask
        fields = '__all__'