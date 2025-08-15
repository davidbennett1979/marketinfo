from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging
from scrapers.ipo_scraper import IPOScraper
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ipo", tags=["ipo"])

# Initialize IPO scraper
ipo_scraper = IPOScraper()

@router.get("/upcoming")
async def get_upcoming_ipos(
    days_ahead: int = Query(default=30, ge=1, le=90, description="Number of days to look ahead for IPOs")
) -> List[Dict[str, Any]]:
    """
    Get upcoming IPO listings for the specified number of days.
    
    Args:
        days_ahead: Number of days to look ahead (1-90 days)
        
    Returns:
        List of upcoming IPOs with company details, dates, and pricing info
    """
    try:
        logger.info(f"Fetching upcoming IPOs for next {days_ahead} days")
        ipos = await ipo_scraper.get_upcoming_ipos(days_ahead)
        
        logger.info(f"Retrieved {len(ipos)} upcoming IPOs")
        return ipos
        
    except Exception as e:
        logger.error(f"Error fetching upcoming IPOs: {str(e)}")
        # Return empty list rather than error to prevent frontend crashes
        return []

@router.get("/recent")
async def get_recent_ipos(
    days_back: int = Query(default=30, ge=1, le=90, description="Number of days to look back for completed IPOs")
) -> List[Dict[str, Any]]:
    """
    Get recently completed IPOs with performance metrics.
    
    Args:
        days_back: Number of days to look back (1-90 days)
        
    Returns:
        List of recent IPOs with performance data
    """
    try:
        logger.info(f"Fetching recent IPOs for past {days_back} days")
        ipos = await ipo_scraper.get_recent_ipos(days_back)
        
        logger.info(f"Retrieved {len(ipos)} recent IPOs")
        return ipos
        
    except Exception as e:
        logger.error(f"Error fetching recent IPOs: {str(e)}")
        return []

@router.get("/calendar")
async def get_ipo_calendar() -> Dict[str, Any]:
    """
    Get a comprehensive IPO calendar view with upcoming and recent IPOs.
    
    Returns:
        Dictionary containing upcoming and recent IPO data
    """
    try:
        logger.info("Fetching comprehensive IPO calendar")
        
        # Fetch both upcoming and recent IPOs
        upcoming = await ipo_scraper.get_upcoming_ipos(30)
        recent = await ipo_scraper.get_recent_ipos(30)
        
        calendar_data = {
            'upcoming_ipos': upcoming,
            'recent_ipos': recent,
            'upcoming_count': len(upcoming),
            'recent_count': len(recent),
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"IPO calendar: {len(upcoming)} upcoming, {len(recent)} recent")
        return calendar_data
        
    except Exception as e:
        logger.error(f"Error fetching IPO calendar: {str(e)}")
        return {
            'upcoming_ipos': [],
            'recent_ipos': [],
            'upcoming_count': 0,
            'recent_count': 0,
            'last_updated': datetime.now().isoformat(),
            'error': 'Failed to fetch IPO data'
        }

@router.get("/stats")
async def get_ipo_statistics() -> Dict[str, Any]:
    """
    Get IPO market statistics and trends.
    
    Returns:
        Dictionary with IPO market statistics
    """
    try:
        logger.info("Calculating IPO statistics")
        
        # Get recent IPOs for analysis
        recent_ipos = await ipo_scraper.get_recent_ipos(90)  # Last 3 months
        upcoming_ipos = await ipo_scraper.get_upcoming_ipos(30)
        
        # Calculate basic statistics
        if recent_ipos:
            # Filter out mock data for real statistics
            real_recent = [ipo for ipo in recent_ipos if ipo.get('source') != 'Mock Data']
            
            if real_recent:
                total_performance = sum(ipo.get('change_percent', 0) for ipo in real_recent)
                avg_performance = total_performance / len(real_recent)
                outperforming = sum(1 for ipo in real_recent if ipo.get('change_percent', 0) > 0)
                success_rate = (outperforming / len(real_recent)) * 100
            else:
                # No real data available - return null/zero values
                avg_performance = 0.0
                success_rate = 0.0
        else:
            # No IPO data available
            avg_performance = 0.0
            success_rate = 0.0
        
        stats = {
            'recent_ipo_count': len(recent_ipos),
            'upcoming_ipo_count': len(upcoming_ipos),
            'average_performance_percent': round(avg_performance, 1),
            'success_rate_percent': round(success_rate, 1),
            'market_trend': 'bullish' if avg_performance > 0 else 'bearish',
            'period_analyzed_days': 90,
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"IPO statistics calculated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating IPO statistics: {str(e)}")
        return {
            'recent_ipo_count': 0,
            'upcoming_ipo_count': 0,
            'average_performance_percent': 0.0,
            'success_rate_percent': 50.0,
            'market_trend': 'neutral',
            'period_analyzed_days': 90,
            'last_updated': datetime.now().isoformat(),
            'error': 'Failed to calculate IPO statistics'
        }