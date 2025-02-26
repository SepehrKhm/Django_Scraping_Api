import requests
from bs4 import BeautifulSoup
from celery import shared_task
from .models import ScrapeTask

@shared_task(bind=True)
def async_scrape(self, task_id):
    task = ScrapeTask.objects.get(id=task_id)
    
    try:
        response = requests.get(task.url, timeout=30)
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
    return task.result 
