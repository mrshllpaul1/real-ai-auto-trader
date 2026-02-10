"""
Data Export API Routes
Endpoints for exporting trades, portfolio, and performance data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from services.data_export import TradeExporter, PortfolioExporter, PerformanceExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/export', tags=['export'])


@router.get('/trades/csv')
async def export_trades_csv(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    strategy: Optional[str] = Query(None, description="Filter by strategy name"),
    coin: Optional[str] = Query(None, description="Filter by coin/symbol")
):
    """
    Export trades to CSV format
    
    **Features:**
    - Filter by date range, strategy, or coin
    - Includes all trade details, P&L, and fees
    - Compatible with Excel and Google Sheets
    
    **Returns:** CSV file download
    """
    try:
        from config.database import db
        
        # Build query filters
        query = {'user_id': user_id}
        
        if start_date:
            query['timestamp'] = {'$gte': start_date}
        if end_date:
            if 'timestamp' not in query:
                query['timestamp'] = {}
            query['timestamp']['$lte'] = end_date
        if strategy:
            query['strategy'] = strategy
        if coin:
            query['coin'] = coin
        
        # Fetch trades from database
        trades = await db.trades.find(query).sort('timestamp', -1).to_list(length=None)
        
        if not trades:
            raise HTTPException(status_code=404, detail="No trades found matching criteria")
        
        logger.info(f"Exporting {len(trades)} trades to CSV for user {user_id}")
        
        return TradeExporter.export_trades_csv(trades)
        
    except Exception as e:
        logger.error(f"Error exporting trades to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/trades/json')
async def export_trades_json(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    strategy: Optional[str] = Query(None, description="Filter by strategy name"),
    coin: Optional[str] = Query(None, description="Filter by coin/symbol")
):
    """
    Export trades to JSON format
    
    **Features:**
    - Filter by date range, strategy, or coin
    - Includes metadata and export timestamp
    - Easy to import into other systems
    
    **Returns:** JSON file download
    """
    try:
        from config.database import db
        
        # Build query filters
        query = {'user_id': user_id}
        
        if start_date:
            query['timestamp'] = {'$gte': start_date}
        if end_date:
            if 'timestamp' not in query:
                query['timestamp'] = {}
            query['timestamp']['$lte'] = end_date
        if strategy:
            query['strategy'] = strategy
        if coin:
            query['coin'] = coin
        
        # Fetch trades from database
        trades = await db.trades.find(query).sort('timestamp', -1).to_list(length=None)
        
        if not trades:
            raise HTTPException(status_code=404, detail="No trades found matching criteria")
        
        logger.info(f"Exporting {len(trades)} trades to JSON for user {user_id}")
        
        return TradeExporter.export_trades_json(trades)
        
    except Exception as e:
        logger.error(f"Error exporting trades to JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/portfolio/csv')
async def export_portfolio_csv(
    user_id: str = Query(..., description="User ID")
):
    """
    Export current portfolio to CSV format
    
    **Features:**
    - Current holdings with cost basis
    - Unrealized P&L per asset
    - Allocation percentages
    - Compatible with Excel
    
    **Returns:** CSV file download
    """
    try:
        from config.database import db
        
        # Fetch portfolio from database
        portfolio = await db.portfolios.find_one({'user_id': user_id})
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        logger.info(f"Exporting portfolio to CSV for user {user_id}")
        
        return PortfolioExporter.export_portfolio_csv(portfolio)
        
    except Exception as e:
        logger.error(f"Error exporting portfolio to CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/portfolio/json')
async def export_portfolio_json(
    user_id: str = Query(..., description="User ID")
):
    """
    Export current portfolio to JSON format
    
    **Features:**
    - Complete portfolio snapshot
    - Asset details with metrics
    - Total value and P&L
    
    **Returns:** JSON file download
    """
    try:
        from config.database import db
        
        # Fetch portfolio from database
        portfolio = await db.portfolios.find_one({'user_id': user_id})
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        logger.info(f"Exporting portfolio to JSON for user {user_id}")
        
        return PortfolioExporter.export_portfolio_json(portfolio)
        
    except Exception as e:
        logger.error(f"Error exporting portfolio to JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/performance/report')
async def export_performance_report(
    user_id: str = Query(..., description="User ID"),
    format: str = Query('json', description="Export format (csv or json)"),
    days: int = Query(30, description="Number of days to include in report")
):
    """
    Export comprehensive performance report
    
    **Features:**
    - Trade history
    - Portfolio snapshot  
    - Performance metrics (win rate, P&L, Sharpe ratio)
    - All-in-one performance summary
    
    **Parameters:**
    - format: 'csv' or 'json'
    - days: Number of days to include (default 30)
    
    **Returns:** Performance report file download
    """
    try:
        from config.database import db
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch trades
        trades = await db.trades.find({
            'user_id': user_id,
            'timestamp': {'$gte': start_date.isoformat(), '$lte': end_date.isoformat()}
        }).sort('timestamp', -1).to_list(length=None)
        
        # Fetch portfolio
        portfolio = await db.portfolios.find_one({'user_id': user_id}) or {}
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('profit_loss', 0) > 0])
        losing_trades = len([t for t in trades if t.get('profit_loss', 0) < 0])
        
        total_profit = sum(t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) > 0)
        total_loss = abs(sum(t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) < 0))
        
        metrics = {
            'total_pnl': sum(t.get('profit_loss', 0) for t in trades),
            'total_pnl_pct': portfolio.get('total_pnl_pct', 0),
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'avg_profit': (total_profit / winning_trades) if winning_trades > 0 else 0,
            'avg_loss': (total_loss / losing_trades) if losing_trades > 0 else 0,
            'profit_factor': (total_profit / total_loss) if total_loss > 0 else 0,
            'sharpe_ratio': portfolio.get('sharpe_ratio', 0),
            'max_drawdown': portfolio.get('max_drawdown', 0)
        }
        
        logger.info(f"Exporting performance report for user {user_id} ({days} days, {format})")
        
        return PerformanceExporter.export_performance_report(
            trades, portfolio, metrics, format
        )
        
    except Exception as e:
        logger.error(f"Error exporting performance report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/tax-report')
async def export_tax_report(
    user_id: str = Query(..., description="User ID"),
    tax_year: int = Query(..., description="Tax year (e.g., 2025)"),
    format: str = Query('csv', description="Export format (csv or json)")
):
    """
    Export tax report for a specific year
    
    **Features:**
    - All trades in specified tax year
    - Realized gains/losses
    - Cost basis information
    - Compatible with tax software
    
    **Parameters:**
    - tax_year: Year for tax reporting
    - format: 'csv' or 'json'
    
    **Returns:** Tax report file download
    """
    try:
        from config.database import db
        
        # Date range for tax year
        start_date = f"{tax_year}-01-01T00:00:00"
        end_date = f"{tax_year}-12-31T23:59:59"
        
        # Fetch trades for tax year
        trades = await db.trades.find({
            'user_id': user_id,
            'timestamp': {'$gte': start_date, '$lte': end_date}
        }).sort('timestamp', 1).to_list(length=None)
        
        if not trades:
            raise HTTPException(
                status_code=404,
                detail=f"No trades found for tax year {tax_year}"
            )
        
        logger.info(f"Exporting tax report for user {user_id}, year {tax_year}")
        
        filename = f"tax_report_{tax_year}"
        
        if format == 'json':
            return TradeExporter.export_trades_json(trades, filename)
        else:
            return TradeExporter.export_trades_csv(trades, filename)
        
    except Exception as e:
        logger.error(f"Error exporting tax report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get('/formats')
async def get_export_formats():
    """
    Get available export formats and their features
    
    **Returns:** List of available formats with descriptions
    """
    return {
        'formats': [
            {
                'format': 'csv',
                'name': 'CSV (Comma-Separated Values)',
                'description': 'Compatible with Excel, Google Sheets, and other spreadsheet software',
                'use_cases': ['Data analysis', 'Tax reporting', 'Record keeping'],
                'file_extension': '.csv'
            },
            {
                'format': 'json',
                'name': 'JSON (JavaScript Object Notation)',
                'description': 'Structured data format, easy to parse programmatically',
                'use_cases': ['API integration', 'Data backup', 'Custom analysis'],
                'file_extension': '.json'
            }
        ],
        'export_types': [
            {
                'type': 'trades',
                'name': 'Trade History',
                'description': 'Export all your trades with complete details',
                'endpoints': ['/api/export/trades/csv', '/api/export/trades/json']
            },
            {
                'type': 'portfolio',
                'name': 'Portfolio Snapshot',
                'description': 'Export current portfolio holdings and P&L',
                'endpoints': ['/api/export/portfolio/csv', '/api/export/portfolio/json']
            },
            {
                'type': 'performance',
                'name': 'Performance Report',
                'description': 'Comprehensive report with trades, portfolio, and metrics',
                'endpoints': ['/api/export/performance/report']
            },
            {
                'type': 'tax',
                'name': 'Tax Report',
                'description': 'Annual trade report for tax purposes',
                'endpoints': ['/api/export/tax-report']
            }
        ]
    }
