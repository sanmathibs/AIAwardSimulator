"""
Award fetcher - downloads HTML from Fair Work website
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import config


class AwardFetcher:
    """Fetch award documents from Fair Work website"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch_from_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch award HTML from URL

        Args:
            url: Full URL to award page

        Returns:
            Dict with raw_html, award_id, award_name
        """
        response = self.session.get(url, timeout=config.FAIRWORK_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Extract award ID from URL
        award_id = self._extract_award_id(url)

        # Extract award name from title or heading
        award_name = self._extract_award_name(soup)

        return {
            "raw_html": response.text,
            "award_id": award_id,
            "award_name": award_name,
            "source_url": url,
        }

    def fetch_from_award_id(self, award_id: str) -> Dict[str, Any]:
        """
        Fetch award using award ID (e.g., MA000028)

        Args:
            award_id: Award ID like "MA000028"

        Returns:
            Dict with raw_html, award_id, award_name
        """
        url = f"{config.FAIRWORK_BASE_URL}/{award_id}.html"
        return self.fetch_from_url(url)

    def _extract_award_id(self, url: str) -> str:
        """Extract award ID from URL"""
        # URL format: https://awards.fairwork.gov.au/MA000028.html
        parts = url.rstrip("/").split("/")
        filename = parts[-1]
        award_id = filename.replace(".html", "")
        return award_id

    def _extract_award_name(self, soup: BeautifulSoup) -> str:
        """Extract award name from HTML"""
        # Try different possible locations for award name

        # Try h1 tag
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Try title tag
        title = soup.find("title")
        if title:
            return title.get_text(strip=True).replace(" | Fair Work Commission", "")

        # Try meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"]

        return "Unknown Award"
