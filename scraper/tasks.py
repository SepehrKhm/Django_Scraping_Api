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
        task.log('INFO', f'Starting scrape task for {task.url}')
        
        # Check cache first
        cache_key = f"scrape:{task.url}:{task.selector}"
        if cached := cache.get(cache_key):
            task.log('INFO', 'Retrieved result from cache')
            task.result = cached
            task.status = 'SUCCESS'
            task.execution_time = time.time() - start_time
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
        
        # Process elements in parallel for large results
        def process_element(elem):
            return elem.get_text(strip=True)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            data = list(executor.map(process_element, elements))
        
        result = {
            "count": len(elements),
            "data": data,
            "status_code": response.status_code,
            "execution_time": time.time() - start_time
        }
        
        # Cache for 1 hour
        cache.set(cache_key, result, 3600)
        task.result = result
        task.status = 'SUCCESS'
        task.execution_time = time.time() - start_time
        task.save()
        
        task.log('INFO', f'Successfully scraped {len(elements)} elements')
        return result

    except Exception as e:
        task.status = 'FAILURE'
        task.execution_time = time.time() - start_time
        task.result = {'error': str(e)}
        task.log('ERROR', str(e), stack_trace=traceback.format_exc())
        task.save()
        
        if task.retries_left > 0:
            task.retries_left -= 1
            task.save()
            raise self.retry(countdown=2 ** self.request.retries, exc=e)
        return None 