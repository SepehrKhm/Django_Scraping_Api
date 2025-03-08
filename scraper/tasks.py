import httpx
from bs4 import BeautifulSoup
from celery import shared_task
from django.core.cache import cache
from .models import ScrapeTask
from .services.cookie_manager import cookie_manager

@shared_task(bind=True, max_retries=3)
def async_scrape(self, task_id):
    task = ScrapeTask.objects.get(id=task_id)
    
    try:
        # Check cache first
        cache_key = f"scrape:{task.url}:{task.selector}"
        if cached := cache.get(cache_key):
            task.result = cached
            task.status = 'SUCCESS'
            task.save()
            return cached

        # Get valid cookies
        cookies = cookie_manager.get_valid_cookies(task.url)
        
        with httpx.Client(timeout=30.0) as client:
            headers = {}
            if cookies:
                headers['Cookie'] = cookie_manager._format_cookies(cookies)
            
            response = client.get(task.url, headers=headers)
            response.raise_for_status()
            
            # Validate if response is as expected
            if not cookie_manager.validate_cookies(task.url, cookies):
                # Invalidate cookies and retry
                cache.delete(f"cookies:{cookie_manager._get_domain(task.url)}")
                raise self.retry(countdown=2)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(task.selector)
            
            result = {
                "count": len(elements),
                "data": [elem.get_text(strip=True) for elem in elements],
                "status_code": response.status_code
            }
            
            # Cache for 1 hour
            cache.set(cache_key, result, 3600)
            task.result = result
            task.status = 'SUCCESS'
            task.save()
            
        return result

    except Exception as e:
        task.result = {'error': str(e)}
        task.status = 'FAILURE'
        task.save()
        raise self.retry(countdown=2 ** self.request.retries, exc=e) 