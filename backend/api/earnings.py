from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging
from scrapers.earnings_scraper import EarningsScaper
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/earnings", tags=["earnings"])

# Initialize earnings scraper
earnings_scraper = EarningsScaper()

@router.get("/upcoming")
async def get_upcoming_earnings(
    days_ahead: int = Query(default=7, ge=1, le=14, description="Number of days to look ahead for earnings")
) -> List[Dict[str, Any]]:
    """
    Get upcoming earnings announcements for the specified number of days.
    
    Args:
        days_ahead: Number of days to look ahead (1-14 days)
        
    Returns:
        List of upcoming earnings with company details, dates, and estimates
    """
    try:
        logger.info(f"Fetching upcoming earnings for next {days_ahead} days")
        earnings = await earnings_scraper.get_upcoming_earnings(days_ahead)
        
        logger.info(f"Retrieved {len(earnings)} upcoming earnings")
        return earnings
        
    except Exception as e:
        logger.error(f"Error fetching upcoming earnings: {str(e)}")
        # Return empty list rather than error to prevent frontend crashes
        return []

@router.get("/today")
async def get_today_earnings() -> List[Dict[str, Any]]:
    """
    Get earnings announcements for today.
    
    Returns:
        List of today's earnings announcements
    """
    try:
        logger.info("Fetching today's earnings")
        today = datetime.now().strftime('%Y-%m-%d')
        earnings = await earnings_scraper.get_earnings_for_date(today)
        
        logger.info(f"Retrieved {len(earnings)} earnings for today")
        return earnings
        
    except Exception as e:
        logger.error(f"Error fetching today's earnings: {str(e)}")
        return []

@router.get("/tomorrow")
async def get_tomorrow_earnings() -> List[Dict[str, Any]]:
    """
    Get earnings announcements for tomorrow.
    
    Returns:
        List of tomorrow's earnings announcements
    """
    try:
        logger.info("Fetching tomorrow's earnings")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        earnings = await earnings_scraper.get_earnings_for_date(tomorrow)
        
        logger.info(f"Retrieved {len(earnings)} earnings for tomorrow")
        return earnings
        
    except Exception as e:
        logger.error(f"Error fetching tomorrow's earnings: {str(e)}")
        return []

@router.get("/calendar")
async def get_earnings_calendar() -> Dict[str, Any]:
    """
    Get a comprehensive earnings calendar view organized by date.
    
    Returns:
        Dictionary containing earnings organized by date
    """
    try:
        logger.info("Fetching comprehensive earnings calendar")
        
        # Get earnings for the next week
        all_earnings = await earnings_scraper.get_upcoming_earnings(7)
        
        # Organize by date
        calendar_data = {}
        dates_processed = set()
        
        for earning in all_earnings:
            date = earning.get('date', '')
            if date and date not in dates_processed:
                date_earnings = [e for e in all_earnings if e.get('date') == date]
                
                # Parse date for better formatting
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                    day_name = date_obj.strftime('%A')
                except:
                    formatted_date = date
                    day_name = 'Unknown'
                
                calendar_data[date] = {
                    'date': date,
                    'formatted_date': formatted_date,
                    'day_name': day_name,
                    'earnings': date_earnings,
                    'count': len(date_earnings)
                }
                dates_processed.add(date)
        
        result = {
            'calendar': calendar_data,
            'total_earnings': len(all_earnings),
            'dates_with_earnings': len(calendar_data),
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"Earnings calendar: {len(all_earnings)} total, {len(calendar_data)} dates")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching earnings calendar: {str(e)}")
        return {
            'calendar': {},
            'total_earnings': 0,
            'dates_with_earnings': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Failed to fetch earnings calendar'
        }

@router.get("/stats")
async def get_earnings_statistics() -> Dict[str, Any]:
    """
    Get earnings calendar statistics and trends.
    
    Returns:
        Dictionary with earnings statistics
    """
    try:
        logger.info("Calculating earnings statistics")
        
        # Get earnings for analysis
        upcoming_earnings = await earnings_scraper.get_upcoming_earnings(7)
        today_earnings = await earnings_scraper.get_earnings_for_date(datetime.now().strftime('%Y-%m-%d'))
        
        # Count by time of day
        before_market = sum(1 for e in upcoming_earnings if 'before' in e.get('time', '').lower())
        after_market = sum(1 for e in upcoming_earnings if 'after' in e.get('time', '').lower())
        during_market = len(upcoming_earnings) - before_market - after_market
        
        # Get unique sectors/companies (mock for now)
        unique_companies = len(set(e.get('symbol', '') for e in upcoming_earnings))
        
        stats = {
            'total_upcoming_earnings': len(upcoming_earnings),
            'today_earnings_count': len(today_earnings),
            'before_market_count': before_market,
            'after_market_count': after_market,
            'during_market_count': during_market,
            'unique_companies': unique_companies,
            'most_common_time': 'after_market' if after_market > before_market else 'before_market',
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"Earnings statistics calculated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating earnings statistics: {str(e)}")
        return {
            'total_upcoming_earnings': 0,
            'today_earnings_count': 0,
            'before_market_count': 0,
            'after_market_count': 0,
            'during_market_count': 0,
            'unique_companies': 0,
            'most_common_time': 'after_market',
            'last_updated': datetime.now().isoformat(),
            'error': 'Failed to calculate earnings statistics'
        }