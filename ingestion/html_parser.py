"""
HTML parser - extracts structured clauses from award HTML
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re


class HTMLParser:
    """Parse Fair Work award HTML into structured clauses"""

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML into structured clauses

        Args:
            html: Raw HTML string

        Returns:
            List of clause dicts with id, title, text, metadata
        """
        soup = BeautifulSoup(html, "lxml")
        clauses = []

        # Find main content area (varies by Fair Work structure)
        content = self._find_main_content(soup)

        if not content:
            # Fallback: use body
            content = soup.find("body")

        # Extract clauses based on headings and structure
        clause_id = 0
        current_section = "Introduction"

        # Find all potential clause elements
        for element in content.find_all(["h1", "h2", "h3", "h4", "p", "div"]):
            # Check if it's a heading
            if element.name in ["h1", "h2", "h3", "h4"]:
                current_section = element.get_text(strip=True)

                # Check if heading contains clause number
                clause_match = re.match(r"(\d+(?:\.\d+)*)\s+(.*)", current_section)
                if clause_match:
                    clause_num = clause_match.group(1)
                    clause_title = clause_match.group(2)

                    # Get following paragraphs until next heading
                    clause_text = self._get_clause_text(element)

                    if clause_text:
                        clause_id += 1
                        clauses.append(
                            {
                                "clause_id": clause_num,
                                "title": clause_title,
                                "text": clause_text,
                                "section": current_section,
                                "metadata": {
                                    "element_type": element.name,
                                    "internal_id": clause_id,
                                },
                            }
                        )

            # Also capture standalone paragraphs with clause numbers
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text and re.match(r"^\d+(?:\.\d+)*\s+", text):
                    clause_match = re.match(r"(\d+(?:\.\d+)*)\s+(.*)", text)
                    if clause_match:
                        clause_num = clause_match.group(1)
                        clause_text = clause_match.group(2)

                        clause_id += 1
                        clauses.append(
                            {
                                "clause_id": clause_num,
                                "title": f"Clause {clause_num}",
                                "text": clause_text,
                                "section": current_section,
                                "metadata": {
                                    "element_type": "paragraph",
                                    "internal_id": clause_id,
                                },
                            }
                        )

        # If no structured clauses found, chunk by paragraphs
        if not clauses:
            clauses = self._fallback_paragraph_chunking(content)

        return clauses

    def _find_main_content(self, soup: BeautifulSoup) -> Any:
        """Find the main content area of the page"""
        # Try common content containers
        selectors = [
            {"id": "content"},
            {"id": "main-content"},
            {"class": "award-content"},
            {"class": "main-content"},
            {"role": "main"},
            {"tag": "main"},
            {"tag": "article"},
        ]

        for selector in selectors:
            if "id" in selector:
                element = soup.find(attrs={"id": selector["id"]})
                if element:
                    return element
            elif "class" in selector:
                element = soup.find(attrs={"class": selector["class"]})
                if element:
                    return element
            elif "role" in selector:
                element = soup.find(attrs={"role": selector["role"]})
                if element:
                    return element
            elif "tag" in selector:
                element = soup.find(selector["tag"])
                if element:
                    return element

        return None

    def _get_clause_text(self, heading_element) -> str:
        """Get text content following a heading"""
        texts = []

        # Get all siblings until next heading
        for sibling in heading_element.find_next_siblings():
            if sibling.name in ["h1", "h2", "h3", "h4"]:
                break

            text = sibling.get_text(strip=True)
            if text:
                texts.append(text)

        return "\n".join(texts)

    def _fallback_paragraph_chunking(self, content) -> List[Dict[str, Any]]:
        """Fallback: chunk by paragraphs if no structure found"""
        clauses = []
        paragraphs = content.find_all("p")

        for idx, para in enumerate(paragraphs):
            text = para.get_text(strip=True)
            if text and len(text) > 50:  # Skip very short paragraphs
                clauses.append(
                    {
                        "clause_id": f"para_{idx + 1}",
                        "title": f"Paragraph {idx + 1}",
                        "text": text,
                        "section": "Content",
                        "metadata": {
                            "element_type": "paragraph",
                            "internal_id": idx + 1,
                        },
                    }
                )

        return clauses
