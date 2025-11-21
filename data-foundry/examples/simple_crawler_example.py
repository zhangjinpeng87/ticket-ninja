"""
Simple WebCrawler example - quick reference.

This is a minimal example showing how to use the WebCrawler.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawler import WebCrawler
from app.services.parser import ContentProcessor


async def main():
    # Create crawler and processor instances
    crawler = WebCrawler(timeout=15.0)
    processor = ContentProcessor()
    
    # Crawl a documentation site
    pages, errors = await crawler.crawl(
        root_url="https://docs.python.org/3/",
        max_depth=1,          # How many link levels to follow
        max_pages=5,          # Maximum number of pages to crawl
        allowed_domains=None, # None = use root domain automatically
        include_subdomains=True,  # Allow subdomains
        skip_assets=True,     # Skip images, CSS, JS files
    )
    
    # Print results
    print(f"Crawled {len(pages)} pages")
    if errors:
        print(f"Encountered {len(errors)} errors")
    
    # Display each page
    for page in pages:
        print(f"\n📄 {page.title}")
        print(f"   URL: {page.url}")
        print(f"   Depth: {page.depth}")
        print(f"   HTML size: {len(page.html)} characters")
        
        # Extract and print text content using ContentProcessor
        text = processor.extract_text(page.html)
        
        # Print first 500 characters of content
        content_preview = text[:500] + "..." if len(text) > 500 else text
        print(f"\n   Content preview ({len(text)} chars total):")
        print(f"   {content_preview}")


if __name__ == "__main__":
    asyncio.run(main())

