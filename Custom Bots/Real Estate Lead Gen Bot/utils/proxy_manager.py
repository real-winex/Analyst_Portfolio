import random
import time
import requests
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta

class ProxyManager:
    def __init__(self, proxy_list: List[str] = None):
        """
        Initialize the proxy manager.
        
        Args:
            proxy_list: List of proxy URLs in format 'http://user:pass@host:port'
                       If None, will try to load from proxy providers
        """
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        self.last_proxy_refresh = datetime.now()
        self.refresh_interval = timedelta(hours=1)  # Refresh proxy list every hour
        self.bad_proxies = set()  # Track failed proxies
        self.max_failures = 3  # Number of failures before removing proxy
        self.proxy_failures = {}  # Track failure count per proxy
        
        if proxy_list:
            self.proxies = proxy_list
        
    def _format_proxy(self, proxy: str) -> Dict[str, str]:
        """Convert proxy string to dictionary format."""
        return {
            'http': proxy,
            'https': proxy.replace('http://', 'https://')
        }

    def _test_proxy(self, proxy: str) -> bool:
        """Test if a proxy is working."""
        try:
            test_url = 'http://httpbin.org/ip'
            formatted_proxy = self._format_proxy(proxy)
            response = requests.get(
                test_url,
                proxies=formatted_proxy,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def _load_webshare_proxies(self, api_key: str) -> List[str]:
        """Load proxies from Webshare."""
        try:
            response = requests.get(
                'https://proxy.webshare.io/api/proxy/list/',
                headers={'Authorization': f'Token {api_key}'}
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    f"http://{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['ports']['http']}"
                    for proxy in data['results']
                ]
        except Exception as e:
            self.logger.error(f"Error loading Webshare proxies: {str(e)}")
        return []

    def _load_proxyscrape_proxies(self, api_key: str) -> List[str]:
        """Load proxies from ProxyScrape."""
        try:
            response = requests.get(
                f'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&format=json&authorization={api_key}'
            )
            if response.status_code == 200:
                data = response.json()
                return [f"http://{proxy['ip']}:{proxy['port']}" for proxy in data['proxies']]
        except Exception as e:
            self.logger.error(f"Error loading ProxyScrape proxies: {str(e)}")
        return []

    def _load_proxy_list(self) -> None:
        """Load and verify proxies from various sources."""
        new_proxies = []
        
        # Load from environment variables or config
        proxy_sources = {
            'WEBSHARE_API_KEY': self._load_webshare_proxies,
            'PROXYSCRAPE_API_KEY': self._load_proxyscrape_proxies,
            # Add more proxy providers as needed
        }
        
        for env_var, loader_func in proxy_sources.items():
            api_key = os.getenv(env_var)
            if api_key:
                new_proxies.extend(loader_func(api_key))
        
        # Test each proxy
        working_proxies = []
        for proxy in new_proxies:
            if self._test_proxy(proxy):
                working_proxies.append(proxy)
                self.logger.info(f"Added working proxy: {proxy}")
            else:
                self.logger.warning(f"Skipping non-working proxy: {proxy}")
        
        self.proxies = working_proxies
        self.last_proxy_refresh = datetime.now()
        self.logger.info(f"Loaded {len(self.proxies)} working proxies")

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random working proxy."""
        # Refresh proxy list if needed
        if (datetime.now() - self.last_proxy_refresh) > self.refresh_interval:
            self._load_proxy_list()
        
        # Remove proxies that have failed too many times
        for proxy in list(self.proxy_failures.keys()):
            if self.proxy_failures[proxy] >= self.max_failures:
                self.bad_proxies.add(proxy)
                self.proxies.remove(proxy)
                del self.proxy_failures[proxy]
                self.logger.warning(f"Removed failing proxy: {proxy}")
        
        # If running low on proxies, refresh the list
        if len(self.proxies) < 5:
            self._load_proxy_list()
        
        if not self.proxies:
            self.logger.error("No working proxies available!")
            return None
        
        # Get a random proxy that isn't in the bad list
        working_proxies = [p for p in self.proxies if p not in self.bad_proxies]
        if not working_proxies:
            self.logger.warning("All proxies are marked as bad, resetting bad proxy list")
            self.bad_proxies.clear()
            working_proxies = self.proxies
        
        proxy = random.choice(working_proxies)
        return self._format_proxy(proxy)

    def report_failure(self, proxy: Dict[str, str]) -> None:
        """Report a proxy failure."""
        proxy_str = proxy['http']
        self.proxy_failures[proxy_str] = self.proxy_failures.get(proxy_str, 0) + 1
        self.logger.warning(f"Proxy failure reported: {proxy_str}")

    def report_success(self, proxy: Dict[str, str]) -> None:
        """Report a proxy success."""
        proxy_str = proxy['http']
        if proxy_str in self.proxy_failures:
            del self.proxy_failures[proxy_str]
        if proxy_str in self.bad_proxies:
            self.bad_proxies.remove(proxy_str)
            self.logger.info(f"Proxy removed from bad list: {proxy_str}")

    def add_proxies(self, new_proxies: List[str]) -> None:
        """Add new proxies to the pool."""
        for proxy in new_proxies:
            if proxy not in self.proxies and self._test_proxy(proxy):
                self.proxies.append(proxy)
                self.logger.info(f"Added new proxy: {proxy}")

    def remove_proxy(self, proxy: str) -> None:
        """Remove a proxy from the pool."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.logger.info(f"Removed proxy: {proxy}")
            if proxy in self.proxy_failures:
                del self.proxy_failures[proxy]
            if proxy in self.bad_proxies:
                self.bad_proxies.remove(proxy) 