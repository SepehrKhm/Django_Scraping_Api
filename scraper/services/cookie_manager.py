import httpx
from playwright.sync_api import sync_playwright
from django.core.cache import cache
from scraper.models import SiteCookie
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class CookieManager:
    def __init__(self):
        self.cache_timeout = 1800  # 30 minutes

    def _get_domain(self, url):
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc

    def _extract_cookies_with_playwright(self, url):
        """Extract cookies using Playwright"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="networkidle")
                cookies = context.cookies()
                
                # Convert cookies to dictionary format
                cookie_dict = {
                    cookie["name"]: {
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "expires": cookie.get("expires", None),
                        "httpOnly": cookie.get("httpOnly", False),
                        "secure": cookie.get("secure", False)
                    } for cookie in cookies
                }
                
                return cookie_dict
            finally:
                browser.close()

    def get_valid_cookies(self, url):
        """Get valid cookies for a domain"""
        domain = self._get_domain(url)
        cache_key = f"cookies:{domain}"

        # Try to get from cache first
        if cached := cache.get(cache_key):
            return cached

        # Try to get from database
        site_cookie = SiteCookie.objects.filter(domain=domain, is_valid=True).first()

        if site_cookie and not site_cookie.is_expired:
            # Cache and return existing cookies
            cache.set(cache_key, site_cookie.cookies, self.cache_timeout)
            return site_cookie.cookies

        # Need to fetch new cookies
        try:
            new_cookies = self._extract_cookies_with_playwright(url)
            
            # Update or create cookie record
            SiteCookie.objects.update_or_create(
                domain=domain,
                defaults={
                    'cookies': new_cookies,
                    'is_valid': True
                }
            )

            # Cache the new cookies
            cache.set(cache_key, new_cookies, self.cache_timeout)
            return new_cookies

        except Exception as e:
            logger.error(f"Error extracting cookies for {url}: {str(e)}")
            return None

    def validate_cookies(self, url, cookies):
        """Validate if cookies are still working"""
        try:
            with httpx.Client() as client:
                headers = {'Cookie': self._format_cookies(cookies)}
                response = client.get(url, headers=headers, follow_redirects=True)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error validating cookies: {str(e)}")
            return False

    def _format_cookies(self, cookies):
        """Format cookies dictionary into string for headers"""
        return '; '.join(f"{name}={cookie['value']}" 
                        for name, cookie in cookies.items())

cookie_manager = CookieManager() 