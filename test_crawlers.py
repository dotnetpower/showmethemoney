"""Test updated crawlers with yfinance enrichment"""
import asyncio
import sys

sys.path.insert(0, 'backend')

from app.services.crawlers.alphaarchitect import AlphaArchitectCrawler
from app.services.crawlers.direxion import DirexionCrawler
from app.services.crawlers.firsttrust import FirstTrustCrawler
from app.services.crawlers.franklintempleton import FranklinTempletonCrawler
from app.services.crawlers.globalx import GlobalXCrawler
from app.services.crawlers.invesco import InvescoCrawler
from app.services.crawlers.pimco import PIMCOCrawler
from app.services.crawlers.roundhill import RoundhillCrawler


async def test_crawler(name, crawler_class):
    """Test a single crawler"""
    print(f"\n{'='*80}")
    print(f"Testing {name} Crawler")
    print('='*80)
    
    try:
        crawler = crawler_class()
        etfs = await crawler.crawl()
        
        if not etfs:
            print(f"⚠️  No ETFs collected")
            return None
        
        # Calculate statistics
        total = len(etfs)
        with_nav = sum(1 for etf in etfs if etf.nav_amount and etf.nav_amount != 0)
        with_expense = sum(1 for etf in etfs if etf.expense_ratio and etf.expense_ratio != 0)
        
        nav_percent = with_nav / total * 100 if total > 0 else 0
        expense_percent = with_expense / total * 100 if total > 0 else 0
        
        print(f"✓ Total ETFs: {total}")
        print(f"✓ With NAV: {with_nav}/{total} ({nav_percent:.1f}%)")
        print(f"✓ With Expense: {with_expense}/{total} ({expense_percent:.1f}%)")
        
        # Show sample data
        print(f"\nSample data (first 3):")
        for i, etf in enumerate(etfs[:3], 1):
            print(f"  {i}. {etf.ticker}: NAV=${etf.nav_amount}, Expense={etf.expense_ratio}%")
        
        return {
            'name': name,
            'total': total,
            'with_nav': with_nav,
            'nav_percent': nav_percent,
            'with_expense': with_expense,
            'expense_percent': expense_percent
        }
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Test all updated crawlers"""
    crawlers = [
        ('PIMCO', PIMCOCrawler),
        ('Alpha Architect', AlphaArchitectCrawler),
        ('FirstTrust', FirstTrustCrawler),
        ('Invesco', InvescoCrawler),
        ('GlobalX', GlobalXCrawler),
        ('Franklin Templeton', FranklinTempletonCrawler),
        ('Roundhill', RoundhillCrawler),
        ('Direxion', DirexionCrawler),
    ]
    
    results = []
    for name, crawler_class in crawlers:
        result = await test_crawler(name, crawler_class)
        if result:
            results.append(result)
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("SUMMARY - NAV Enrichment Results")
    print('='*80)
    print(f"{'Provider':<20} {'Total':>8} {'With NAV':>10} {'NAV %':>10} {'Expense %':>12}")
    print('-'*80)
    
    total_all = 0
    total_nav = 0
    total_expense = 0
    
    for result in results:
        print(f"{result['name']:<20} {result['total']:>8} {result['with_nav']:>10} "
              f"{result['nav_percent']:>9.1f}% {result['expense_percent']:>11.1f}%")
        total_all += result['total']
        total_nav += result['with_nav']
        total_expense += result['with_expense']
    
    print('='*80)
    overall_nav = total_nav / total_all * 100 if total_all > 0 else 0
    overall_expense = total_expense / total_all * 100 if total_all > 0 else 0
    print(f"{'TOTAL':<20} {total_all:>8} {total_nav:>10} {overall_nav:>9.1f}% {overall_expense:>11.1f}%")
    print('='*80)


if __name__ == '__main__':
    asyncio.run(main())
