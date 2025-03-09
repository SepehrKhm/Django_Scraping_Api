import time
import traceback
import requests
from bs4 import BeautifulSoup
from celery import shared_task
from django.core.cache import cache
from .models import ScrapeTask
from .services.cookie_manager import cookie_manager
from concurrent.futures import ThreadPoolExecutor

@shared_task(bind=True, max_retries=3)
def sync_scrape(self, task_id):
    start_time = time.time()
    task = ScrapeTask.objects.get(id=task_id)
    
    try:
        # Check if task was interrupted
        if task.status in ['INTERRUPTED', 'PAUSED']:
            task.log('INFO', f'Resuming task from position {task.current_position}')
        else:
            task.current_position = 0
            task.progress = 0
        
        task.status = 'IN_PROGRESS'
        task.save()
        
        # Cache check
        cache_key = f"scrape:{task.url}:{task.selector}"
        if cached := cache.get(cache_key):
            task.log('INFO', 'Retrieved result from cache')
            task.result = cached
            task.status = 'SUCCESS'
            task.progress = 100
            task.save()
            return cached

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        if task.requires_cookies:
            task.log('INFO', 'Fetching cookies')
            cookies = cookie_manager.get_valid_cookies(task.url)
            if cookies:
                headers['Cookie'] = cookie_manager._format_cookies(cookies)
        
        # Make the request with timeout
        task.log('INFO', 'Making HTTP request')
        response = requests.get(task.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if task.requires_cookies and headers.get('Cookie'):
            if not cookie_manager.validate_cookies(task.url, cookies):
                task.log('WARNING', 'Cookie validation failed, retrying')
                cache.delete(f"cookies:{cookie_manager._get_domain(task.url)}")
                raise self.retry(countdown=2)
        
        # Parse HTML
        task.log('INFO', 'Parsing HTML response')
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select(task.selector)
        
        task.total_items = len(elements)
        task.save()
        
        # Process elements with progress tracking
        data = []
        for i, elem in enumerate(elements[task.current_position:], task.current_position):
            try:
                data.append(elem.get_text(strip=True))
                task.current_position = i + 1
                task.progress = (i + 1) * 100 / len(elements)
                task.save()
                
                # Periodic save to prevent data loss
                if i % 10 == 0:  # Save every 10 items
                    result = {
                        "count": len(data),
                        "data": data,
                        "status_code": response.status_code,
                        "execution_time": time.time() - start_time
                    }
                    task.result = result
                    task.save()
                    
            except Exception as e:
                task.log('WARNING', f'Error processing element {i}: {str(e)}')
                continue
        
        result = {
            "count": len(data),
            "data": data,
            "status_code": response.status_code,
            "execution_time": time.time() - start_time,
            "completed": True
        }
        
        # Cache final result
        cache.set(cache_key, result, 3600)
        task.result = result
        task.status = 'SUCCESS'
        task.progress = 100
        task.save()
        
        task.log('INFO', f'Successfully scraped {len(data)} elements')
        return result

    except Exception as e:
        task.status = 'INTERRUPTED' if isinstance(e, (ConnectionError, TimeoutError)) else 'FAILURE'
        task.execution_time = time.time() - start_time
        task.result = {'error': str(e)}
        task.log('ERROR', str(e), stack_trace=traceback.format_exc())
        task.save()
        
        if task.retries_left > 0:
            task.retries_left -= 1
            task.save()
            raise self.retry(countdown=2 ** self.request.retries, exc=e)
        return None 