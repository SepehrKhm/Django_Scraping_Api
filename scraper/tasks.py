import time
import traceback
import requests
from bs4 import BeautifulSoup
from celery import shared_task
from django.core.cache import cache
from .models import ScrapeTask, ScrapeResult
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
        
        # Parse HTML for each selector
        soup = BeautifulSoup(response.text, 'html.parser')
        all_results = []
        total_elements = 0

        for selector in task.selectors:
            task.log('INFO', f'Processing selector: {selector}')
            elements = soup.select(selector)
            total_elements += len(elements)
            
            # Process elements with progress tracking
            for i, elem in enumerate(elements):
                try:
                    content = elem.get_text(strip=True)
                    # Store result in database
                    ScrapeResult.objects.create(
                        task=task,
                        selector=selector,
                        content=content,
                        metadata={
                            'position': i,
                            'selector_index': task.selectors.index(selector),
                            'html': elem.decode_contents()
                        }
                    )
                    all_results.append({
                        'selector': selector,
                        'content': content
                    })
                    
                    # Update progress
                    task.current_position = len(all_results)
                    task.progress = (len(all_results) * 100) / total_elements
                    task.save()
                    
                except Exception as e:
                    task.log('WARNING', f'Error processing element {i} for selector {selector}: {str(e)}')
                    continue

        # Store final result
        result = {
            "count": len(all_results),
            "results_by_selector": {},
            "status_code": response.status_code,
            "execution_time": time.time() - start_time,
            "completed": True
        }

        # Group results by selector
        for selector in task.selectors:
            result["results_by_selector"][selector] = [
                r['content'] for r in all_results 
                if r['selector'] == selector
            ]

        task.result = result
        task.status = 'SUCCESS'
        task.progress = 100
        task.save()
        
        task.log('INFO', f'Successfully scraped {len(all_results)} elements across {len(task.selectors)} selectors')
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