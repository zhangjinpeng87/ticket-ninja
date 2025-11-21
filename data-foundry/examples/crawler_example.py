"""
Example usage of the WebCrawler class.

This script demonstrates how to use the WebCrawler to crawl documentation sites
and inspect the results before ingesting them into the knowledge base.
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawler import WebCrawler


async def example_basic_crawl():
    """Basic example: crawl a documentation site"""
    print("=" * 60)
    print("Example 1: Basic Crawl")
    print("=" * 60)
    
    crawler = WebCrawler(timeout=15.0)
    
    pages, errors = await crawler.crawl(
        root_url="https://docs.python.org/3/",
        max_depth=1,
        max_pages=5,
        allowed_domains=None,  # Will use root domain
        include_subdomains=True,
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages")
    print(f"⚠️  {len(errors)} errors encountered\n")
    
    for page in pages:
        print(f"  - [{page.depth}] {page.title[:60]}")
        print(f"    URL: {page.url}")
        print(f"    Content length: {len(page.html)} chars\n")
    
    if errors:
        print("Errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")


async def example_restricted_domain():
    """Example: restrict crawling to specific domains"""
    print("\n" + "=" * 60)
    print("Example 2: Restricted Domain Crawl")
    print("=" * 60)
    
    crawler = WebCrawler()
    
    pages, errors = await crawler.crawl(
        root_url="https://kubernetes.io/docs/",
        max_depth=2,
        max_pages=10,
        allowed_domains=["kubernetes.io"],  # Only crawl kubernetes.io
        include_subdomains=True,  # Allow docs.kubernetes.io, etc.
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages from kubernetes.io")
    print(f"⚠️  {len(errors)} errors\n")
    
    # Group by depth
    by_depth = {}
    for page in pages:
        by_depth.setdefault(page.depth, []).append(page)
    
    for depth in sorted(by_depth.keys()):
        print(f"Depth {depth}: {len(by_depth[depth])} pages")


async def example_no_subdomains():
    """Example: crawl only exact domain, no subdomains"""
    print("\n" + "=" * 60)
    print("Example 3: Exact Domain Only (No Subdomains)")
    print("=" * 60)
    
    crawler = WebCrawler()
    
    pages, errors = await crawler.crawl(
        root_url="https://www.postgresql.org/docs/",
        max_depth=1,
        max_pages=5,
        allowed_domains=["www.postgresql.org"],
        include_subdomains=False,  # Don't crawl other subdomains
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages")
    print(f"Domains visited:")
    domains = set()
    for page in pages:
        from urllib.parse import urlparse
        domain = urlparse(page.url).netloc
        domains.add(domain)
    for domain in sorted(domains):
        print(f"  - {domain}")


async def example_deep_crawl():
    """Example: deeper crawl with more pages"""
    print("\n" + "=" * 60)
    print("Example 4: Deep Crawl (Higher Depth)")
    print("=" * 60)
    
    crawler = WebCrawler()
    
    pages, errors = await crawler.crawl(
        root_url="https://fastapi.tiangolo.com/",
        max_depth=3,  # Go 3 levels deep
        max_pages=20,  # Up to 20 pages
        allowed_domains=None,
        include_subdomains=True,
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages")
    
    # Show depth distribution
    depth_counts = {}
    for page in pages:
        depth_counts[page.depth] = depth_counts.get(page.depth, 0) + 1
    
    print("\nDepth distribution:")
    for depth in sorted(depth_counts.keys()):
        print(f"  Depth {depth}: {depth_counts[depth]} pages")


async def example_error_handling():
    """Example: demonstrate error handling"""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    crawler = WebCrawler(timeout=5.0)  # Shorter timeout to trigger errors
    
    # Try crawling a site that might have issues
    pages, errors = await crawler.crawl(
        root_url="https://httpstat.us/500",  # This will return 500
        max_depth=1,
        max_pages=5,
        allowed_domains=None,
        include_subdomains=True,
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages")
    print(f"⚠️  {len(errors)} errors encountered\n")
    
    if errors:
        print("Error details:")
        for error in errors:
            print(f"  - {error}")


async def example_inspect_content():
    """Example: inspect crawled content before processing"""
    print("\n" + "=" * 60)
    print("Example 6: Inspect Crawled Content")
    print("=" * 60)
    
    crawler = WebCrawler()
    
    pages, errors = await crawler.crawl(
        root_url="https://docs.docker.com/",
        max_depth=1,
        max_pages=3,
        allowed_domains=None,
        include_subdomains=True,
        skip_assets=True,
    )
    
    print(f"\n✅ Crawled {len(pages)} pages\n")
    
    for page in pages:
        # Extract a preview of the content
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.html, "lxml")
        
        # Get text content (first 200 chars)
        text = soup.get_text(strip=True)
        preview = text[:200] + "..." if len(text) > 200 else text
        
        print(f"Page: {page.title}")
        print(f"URL: {page.url}")
        print(f"Text preview: {preview}\n")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("WebCrawler Usage Examples")
    print("=" * 60)
    print("\nThese examples demonstrate different ways to use the WebCrawler.")
    print("Note: Some examples crawl real websites - be respectful of rate limits!\n")
    
    examples = [
        ("Basic Crawl", example_basic_crawl),
        ("Restricted Domain", example_restricted_domain),
        ("No Subdomains", example_no_subdomains),
        ("Deep Crawl", example_deep_crawl),
        ("Error Handling", example_error_handling),
        ("Inspect Content", example_inspect_content),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}\n")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

