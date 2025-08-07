from app.scrapers.baliExceptionScraper import BaliExceptionScraper

def test_multi_category_scraper():
    """Test multi-category scraping"""
    try:
        print("=== TESTING MULTI-CATEGORY SCRAPING ===")
        
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            # Test both categories
            urls_by_category = scraper.scrape_all_urls(['for-sale', 'for-rent'])
            
            print("\n=== RESULTS ===")
            total_urls = 0
            for category, urls in urls_by_category.items():
                print(f"\n{category.upper()}:")
                print(f"  Total URLs: {len(urls)}")
                total_urls += len(urls)
                
                # Print first 3 URLs as examples
                for i, url in enumerate(urls[:3]):
                    print(f"  {i+1}. {url}")
                if len(urls) > 3:
                    print(f"  ... and {len(urls) - 3} more")
            
            print(f"\nGRAND TOTAL: {total_urls} URLs across all categories")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_single_category():
    """Test single category scraping"""
    print("\n=== TESTING SINGLE CATEGORY (FOR-RENT ONLY) ===")
    
    try:
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            # Test only for-rent
            urls_by_category = scraper.scrape_all_urls(['for-rent'])
            
            for category, urls in urls_by_category.items():
                print(f"\n{category.upper()}:")
                print(f"  Total URLs: {len(urls)}")
                
                # Print first 5 URLs
                for i, url in enumerate(urls[:5]):
                    print(f"  {i+1}. {url}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_property_details():
    """Test property details extraction"""
    print("\n=== TESTING PROPERTY DETAILS EXTRACTION ===")
    
    # Sample URLs (you need to update these with real URLs)
    test_urls = {
        'for-sale': 'https://baliexception.com/properties/bali-villa-for-sale-ubud',  # Update with real URL
        'for-rent': 'https://villas.baliexception.com/listings/villa-sample'  # Update with real URL
    }
    
    try:
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            for category, url in test_urls.items():
                print(f"\nTesting {category} property details:")
                print(f"URL: {url}")
                
                # Get property details using category-specific scraper
                results = scraper.scrape_property_details([url], category)
                
                if results:
                    property_data = results[0]
                    print(f"Title: {property_data.get('title', 'N/A')}")
                    print(f"Price IDR: {property_data.get('price_idr', 'N/A')}")
                    print(f"Price USD: {property_data.get('price_usd', 'N/A')}")
                    print(f"Location: {property_data.get('location', 'N/A')}")
                    print(f"Property Type: {property_data.get('property_type', 'N/A')}")
                    print(f"Features: {len(property_data.get('features', {}))}")
                else:
                    print("No data extracted")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run all tests
    test_multi_category_scraper()
    # test_single_category()
    # test_property_details()  # Uncomment after getting real URLs