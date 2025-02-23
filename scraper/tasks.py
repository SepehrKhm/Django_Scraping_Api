import httpx
from bs4 import BeautifulSoup
from celery import shared_task
from .models import ScrapeTask

@shared_task(bind=True)
async def async_scrape(self, task_id):
    task = ScrapeTask.objects.get(id=task_id)
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(task.url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(task.selector)
            
            task.result = {
                'count': len(elements),
                'data': [elem.get_text(strip=True) for elem in elements],
                'status_code': response.status_code
            }
            task.status = 'SUCCESS'
            
    except Exception as e:
        task.result = {'error': str(e)}
        task.status = 'FAILURE'
    
    task.save()