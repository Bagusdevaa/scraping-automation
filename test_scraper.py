from app.scrapers.baliExceptionScraper import BaliExceptionScraper

def test_scraper():
    try:
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            urls = scraper.scrape_all_urls()
            print(f"Found {len(urls)} URLs")
            for i, url in enumerate(urls[:5]):  # Print first 5
                print(f"{i+1}. {url}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scraper()