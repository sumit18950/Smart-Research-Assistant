"""
Web scraping module for fetching and processing web content.
Uses httpx (async) + BeautifulSoup for scraping, with SerpAPI for search.
"""

import re
import httpx
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.logging import logger


class WebScraper:
    def __init__(self):
        settings = get_settings()
        self.serpapi_key = settings.serpapi_key
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Research Assistant Bot)"
        }

    async def search_web(self, query: str, num_results: int = 5) -> list[Document]:
        """Search the web using SerpAPI and return processed documents."""
        logger.info(f"Web search: {query}")

        if not self.serpapi_key:
            logger.warning("SerpAPI key not configured, returning empty results")
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "api_key": self.serpapi_key,
                        "num": num_results,
                        "engine": "google",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI request failed: {e}")
            return []

        documents = []
        for result in data.get("organic_results", [])[:num_results]:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")

            # Try to fetch full page content
            full_text = await self._fetch_page(link)
            content = full_text if full_text else snippet

            doc = Document(
                page_content=content,
                metadata={
                    "title": title,
                    "source": link,
                    "doc_type": "web",
                    "snippet": snippet,
                },
            )
            documents.append(doc)

        # Chunk the web documents
        chunked = []
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            for idx, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = idx
            chunked.extend(chunks)

        logger.info(f"Web search returned {len(chunked)} chunks from {len(documents)} pages")
        return chunked

    async def _fetch_page(self, url: str) -> str:
        """Fetch and extract main text content from a URL."""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Clean up whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            # Limit to ~5000 chars to avoid huge pages
            return text[:5000]
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""
