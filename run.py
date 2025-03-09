import os
import uvicorn

# Set the Django settings module before importing get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraping_project.settings')

from django.core.asgi import get_asgi_application
application = get_asgi_application()

if __name__ == "__main__":
    uvicorn.run(
        "scraping_project.asgi:application",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info",
        reload=True
    ) 