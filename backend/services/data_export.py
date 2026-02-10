"""
Data Export Service
Provides CSV and JSON export functionality for trades, portfolio, and analytics
"""

import csv
import json
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import Response
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """Service for exporting data in various formats"""
    
    @staticmethod
    def to_csv(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
        """
        Convert list of dictionaries to CSV format
        
        Args:
            data: List of dictionaries to export
            columns: Optional list of column names to include (in order)
        
        Returns:
            CSV string
        """
        if not data:
            return ""
        
        # Use provided columns or extract from first row
        if not columns:
            columns = list(data[0].keys())
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    @staticmethod
    def to_json(data: Any, pretty: bool = True) -> str:
        """
        Convert data to JSON format
        
        Args:
            data: Data to export
            pretty: Whether to pretty-print JSON
        
        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    @staticmethod
    def create_csv_response(
        data: List[Dict[str, Any]],
        filename: str,
        columns: Optional[List[str]] = None
    ) -> Response:
        """
        Create a CSV file download response
        
        Args:
            data: Data to export
            filename: Name of the file (without .csv extension)
            columns: Optional list of columns to include
        
        Returns:
            FastAPI Response with CSV file
        """
        csv_content = DataExporter.to_csv(data, columns)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    
    @staticmethod
    def create_json_response(
        data: Any,
        filename: str,
        pretty: bool = True
    ) -> Response:
        """
        Create a JSON file download response
        
        Args:
            data: Data to export
            filename: Name of the file (without .json extension)
            pretty: Whether to pretty-print JSON
        
        Returns:
            FastAPI Response with JSON file
        """
        json_content = DataExporter.to_json(data, pretty)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.json"
            }
        )


class TradeExporter:
    """Specialized exporter for trade data"""
    
    TRADE_COLUMNS = [
        'trade_id',
        'timestamp',
        'coin',
        'action',
        'quantity',
        'price',
        'total_value',
        'fees',
        'profit_loss',
        'profit_loss_pct',
        'strategy',
        'confidence',
        'notes'
    ]
    
    @staticmethod
    def prepare_trade_data(trades: List[Dict]) -> List[Dict[str, Any]]:
        """
        Prepare trade data for export with calculated fields
        
        Args:
            trades: List of trade records
        
        Returns:
            List of formatted trade dictionaries
        """
        formatted_trades = []
        
        for trade in trades:
            formatted_trade = {
                'trade_id': trade.get('_id', trade.get('trade_id', '')),
                'timestamp': trade.get('timestamp', ''),
                'coin': trade.get('coin', trade.get('symbol', '')),
                'action': trade.get('action', trade.get('side', '')).upper(),
                'quantity': trade.get('quantity', trade.get('amount', 0)),
                'price': trade.get('price', trade.get('entry_price', 0)),
                'total_value': trade.get('total_value', 0),
                'fees': trade.get('fees', 0),
                'profit_loss': trade.get('profit_loss', trade.get('pnl', 0)),
                'profit_loss_pct': trade.get('profit_loss_pct', 0),
                'strategy': trade.get('strategy', 'manual'),
                'confidence': trade.get('confidence', 0),
                'notes': trade.get('notes', '')
            }
            
            # Format timestamp if it's a datetime object
            if isinstance(formatted_trade['timestamp'], datetime):
                formatted_trade['timestamp'] = formatted_trade['timestamp'].isoformat()
            
            formatted_trades.append(formatted_trade)
        
        return formatted_trades
    
    @staticmethod
    def export_trades_csv(trades: List[Dict], filename: Optional[str] = None) -> Response:
        """Export trades to CSV file"""
        if not filename:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        formatted_trades = TradeExporter.prepare_trade_data(trades)
        return DataExporter.create_csv_response(
            formatted_trades,
            filename,
            TradeExporter.TRADE_COLUMNS
        )
    
    @staticmethod
    def export_trades_json(trades: List[Dict], filename: Optional[str] = None) -> Response:
        """Export trades to JSON file"""
        if not filename:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        formatted_trades = TradeExporter.prepare_trade_data(trades)
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_trades': len(formatted_trades),
            'trades': formatted_trades
        }
        return DataExporter.create_json_response(export_data, filename)


class PortfolioExporter:
    """Specialized exporter for portfolio data"""
    
    PORTFOLIO_COLUMNS = [
        'coin',
        'quantity',
        'average_cost',
        'current_price',
        'current_value',
        'cost_basis',
        'unrealized_pnl',
        'unrealized_pnl_pct',
        'allocation_pct'
    ]
    
    @staticmethod
    def prepare_portfolio_data(portfolio: Dict) -> List[Dict[str, Any]]:
        """
        Prepare portfolio data for export
        
        Args:
            portfolio: Portfolio data dictionary
        
        Returns:
            List of formatted asset dictionaries
        """
        assets = portfolio.get('assets', portfolio.get('positions', []))
        total_value = portfolio.get('total_value', 0)
        
        formatted_assets = []
        for asset in assets:
            formatted_asset = {
                'coin': asset.get('coin', asset.get('symbol', '')),
                'quantity': asset.get('quantity', asset.get('balance', 0)),
                'average_cost': asset.get('average_cost', asset.get('avg_price', 0)),
                'current_price': asset.get('current_price', asset.get('price', 0)),
                'current_value': asset.get('current_value', asset.get('value', 0)),
                'cost_basis': asset.get('cost_basis', 0),
                'unrealized_pnl': asset.get('unrealized_pnl', asset.get('pnl', 0)),
                'unrealized_pnl_pct': asset.get('unrealized_pnl_pct', 0),
                'allocation_pct': (asset.get('current_value', 0) / total_value * 100) if total_value > 0 else 0
            }
            formatted_assets.append(formatted_asset)
        
        return formatted_assets
    
    @staticmethod
    def export_portfolio_csv(portfolio: Dict, filename: Optional[str] = None) -> Response:
        """Export portfolio to CSV file"""
        if not filename:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        formatted_assets = PortfolioExporter.prepare_portfolio_data(portfolio)
        return DataExporter.create_csv_response(
            formatted_assets,
            filename,
            PortfolioExporter.PORTFOLIO_COLUMNS
        )
    
    @staticmethod
    def export_portfolio_json(portfolio: Dict, filename: Optional[str] = None) -> Response:
        """Export portfolio to JSON file"""
        if not filename:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_value': portfolio.get('total_value', 0),
            'total_cost_basis': portfolio.get('total_cost_basis', 0),
            'total_pnl': portfolio.get('total_pnl', 0),
            'total_pnl_pct': portfolio.get('total_pnl_pct', 0),
            'assets': PortfolioExporter.prepare_portfolio_data(portfolio)
        }
        return DataExporter.create_json_response(export_data, filename)


class PerformanceExporter:
    """Specialized exporter for performance analytics"""
    
    @staticmethod
    def export_performance_report(
        trades: List[Dict],
        portfolio: Dict,
        metrics: Dict,
        format: str = 'json',
        filename: Optional[str] = None
    ) -> Response:
        """
        Export comprehensive performance report
        
        Args:
            trades: List of trades
            portfolio: Portfolio data
            metrics: Performance metrics
            format: Export format ('json' or 'csv')
            filename: Optional filename
        
        Returns:
            FastAPI Response with report file
        """
        if not filename:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = {
            'report_date': datetime.now().isoformat(),
            'summary': {
                'total_trades': len(trades),
                'total_portfolio_value': portfolio.get('total_value', 0),
                'total_pnl': metrics.get('total_pnl', 0),
                'total_pnl_pct': metrics.get('total_pnl_pct', 0),
                'win_rate': metrics.get('win_rate', 0),
                'avg_profit': metrics.get('avg_profit', 0),
                'avg_loss': metrics.get('avg_loss', 0),
                'profit_factor': metrics.get('profit_factor', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0)
            },
            'trades': TradeExporter.prepare_trade_data(trades),
            'portfolio': PortfolioExporter.prepare_portfolio_data(portfolio)
        }
        
        if format == 'csv':
            # For CSV, create separate sheets approach (multiple CSVs)
            # Return trades CSV as primary file
            return TradeExporter.export_trades_csv(trades, filename)
        else:
            return DataExporter.create_json_response(report, filename)


# Convenience function to get exporter
def get_exporter(export_type: str = 'trade'):
    """
    Get appropriate exporter based on type
    
    Args:
        export_type: Type of exporter ('trade', 'portfolio', 'performance')
    
    Returns:
        Exporter class
    """
    exporters = {
        'trade': TradeExporter,
        'portfolio': PortfolioExporter,
        'performance': PerformanceExporter
    }
    return exporters.get(export_type, TradeExporter)
