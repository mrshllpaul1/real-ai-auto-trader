"""
Custom Strategy Builder Service
AI-assisted strategy creation with natural language processing
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import re
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class StrategyTemplate:
    """Pre-built strategy templates"""
    
    TEMPLATES = {
        'momentum': {
            'name': 'Momentum Strategy',
            'description': 'Buy when price momentum is strong, sell when it weakens',
            'indicators': ['rsi', 'macd', 'volume'],
            'entry_conditions': [
                {'indicator': 'rsi', 'operator': '>', 'value': 50},
                {'indicator': 'macd_histogram', 'operator': '>', 'value': 0}
            ],
            'exit_conditions': [
                {'indicator': 'rsi', 'operator': '<', 'value': 40},
                {'indicator': 'macd_histogram', 'operator': '<', 'value': 0}
            ],
            'risk_params': {'stop_loss_pct': 8, 'take_profit_pct': 20, 'position_size_pct': 10}
        },
        'mean_reversion': {
            'name': 'Mean Reversion Strategy',
            'description': 'Buy oversold conditions, sell overbought conditions',
            'indicators': ['rsi', 'bollinger_bands'],
            'entry_conditions': [
                {'indicator': 'rsi', 'operator': '<', 'value': 30},
                {'indicator': 'price_vs_bb_lower', 'operator': '<', 'value': 0}
            ],
            'exit_conditions': [
                {'indicator': 'rsi', 'operator': '>', 'value': 70},
                {'indicator': 'price_vs_bb_upper', 'operator': '>', 'value': 0}
            ],
            'risk_params': {'stop_loss_pct': 5, 'take_profit_pct': 15, 'position_size_pct': 8}
        },
        'breakout': {
            'name': 'Breakout Strategy',
            'description': 'Enter on price breakouts with volume confirmation',
            'indicators': ['atr', 'volume', 'support_resistance'],
            'entry_conditions': [
                {'indicator': 'price_vs_resistance', 'operator': '>', 'value': 0},
                {'indicator': 'volume_ratio', 'operator': '>', 'value': 1.5}
            ],
            'exit_conditions': [
                {'indicator': 'trailing_stop', 'operator': 'triggered', 'value': True}
            ],
            'risk_params': {'stop_loss_pct': 10, 'take_profit_pct': 30, 'position_size_pct': 12}
        },
        'trend_following': {
            'name': 'Trend Following Strategy',
            'description': 'Follow established trends using moving averages',
            'indicators': ['sma_20', 'sma_50', 'sma_200', 'adx'],
            'entry_conditions': [
                {'indicator': 'sma_20', 'operator': '>', 'value': 'sma_50'},
                {'indicator': 'sma_50', 'operator': '>', 'value': 'sma_200'},
                {'indicator': 'adx', 'operator': '>', 'value': 25}
            ],
            'exit_conditions': [
                {'indicator': 'sma_20', 'operator': '<', 'value': 'sma_50'}
            ],
            'risk_params': {'stop_loss_pct': 12, 'take_profit_pct': 40, 'position_size_pct': 15}
        },
        'scalping': {
            'name': 'Scalping Strategy',
            'description': 'Quick trades on small price movements',
            'indicators': ['rsi', 'stochastic', 'volume'],
            'entry_conditions': [
                {'indicator': 'stochastic_k', 'operator': '<', 'value': 20},
                {'indicator': 'volume_spike', 'operator': '>', 'value': True}
            ],
            'exit_conditions': [
                {'indicator': 'stochastic_k', 'operator': '>', 'value': 80},
                {'indicator': 'profit_pct', 'operator': '>', 'value': 2}
            ],
            'risk_params': {'stop_loss_pct': 2, 'take_profit_pct': 3, 'position_size_pct': 20}
        },
        'dca_accumulation': {
            'name': 'DCA Accumulation Strategy',
            'description': 'Dollar-cost averaging with smart entry timing',
            'indicators': ['fear_greed_index', 'rsi', 'price_vs_ath'],
            'entry_conditions': [
                {'indicator': 'fear_greed_index', 'operator': '<', 'value': 30},
                {'indicator': 'rsi', 'operator': '<', 'value': 40}
            ],
            'exit_conditions': [
                {'indicator': 'profit_pct', 'operator': '>', 'value': 50}
            ],
            'risk_params': {'stop_loss_pct': 0, 'take_profit_pct': 100, 'position_size_pct': 5}
        },
        'whale_following': {
            'name': 'Whale Following Strategy',
            'description': 'Follow large wallet movements',
            'indicators': ['whale_activity', 'exchange_flows', 'on_chain'],
            'entry_conditions': [
                {'indicator': 'whale_accumulation', 'operator': '>', 'value': True},
                {'indicator': 'exchange_outflow', 'operator': '>', 'value': 'exchange_inflow'}
            ],
            'exit_conditions': [
                {'indicator': 'whale_distribution', 'operator': '>', 'value': True}
            ],
            'risk_params': {'stop_loss_pct': 15, 'take_profit_pct': 50, 'position_size_pct': 10}
        },
        'sentiment_based': {
            'name': 'Sentiment-Based Strategy',
            'description': 'Trade based on social sentiment and news',
            'indicators': ['social_sentiment', 'news_sentiment', 'fear_greed'],
            'entry_conditions': [
                {'indicator': 'social_sentiment', 'operator': '>', 'value': 60},
                {'indicator': 'news_sentiment', 'operator': '>', 'value': 'neutral'}
            ],
            'exit_conditions': [
                {'indicator': 'social_sentiment', 'operator': '<', 'value': 40}
            ],
            'risk_params': {'stop_loss_pct': 10, 'take_profit_pct': 25, 'position_size_pct': 8}
        }
    }


class CustomStrategyBuilder:
    """
    AI-assisted custom strategy builder
    - Natural language strategy creation
    - Template-based quick start
    - Condition builder with validation
    - Backtesting integration
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, ai_chat_service=None):
        self.db = db
        self.ai_chat = ai_chat_service
        self.templates = StrategyTemplate.TEMPLATES
        
        # Available indicators
        self.available_indicators = {
            'technical': ['rsi', 'macd', 'macd_histogram', 'macd_signal', 'sma_20', 'sma_50', 
                         'sma_200', 'ema_12', 'ema_26', 'bollinger_upper', 'bollinger_lower',
                         'bollinger_middle', 'atr', 'adx', 'stochastic_k', 'stochastic_d',
                         'obv', 'vwap', 'ichimoku_cloud'],
            'volume': ['volume', 'volume_sma', 'volume_ratio', 'volume_spike'],
            'price': ['price', 'price_change_1h', 'price_change_24h', 'price_change_7d',
                     'price_vs_ath', 'price_vs_atl', 'high_24h', 'low_24h'],
            'sentiment': ['fear_greed_index', 'social_sentiment', 'news_sentiment',
                         'twitter_sentiment', 'reddit_sentiment'],
            'on_chain': ['whale_activity', 'exchange_inflow', 'exchange_outflow',
                        'active_addresses', 'nvt_ratio', 'mvrv_ratio'],
            'market': ['btc_dominance', 'market_cap', 'market_cap_rank', 'total_volume']
        }
        
        # Operators
        self.operators = ['>', '<', '>=', '<=', '==', '!=', 'crosses_above', 'crosses_below', 'triggered']
    
    async def build_from_natural_language(self, description: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Build a strategy from natural language description using AI
        
        Args:
            description: Natural language strategy description
            session_id: Chat session ID
            
        Returns:
            Parsed strategy configuration
        """
        if not self.ai_chat:
            return {'error': 'AI chat service not available'}
        
        try:
            # Create a specialized prompt for strategy building
            prompt = f"""You are a trading strategy builder assistant. Parse the following strategy description and convert it into a structured trading strategy.

User's Strategy Description:
"{description}"

Please respond with a JSON object containing:
{{
    "name": "Strategy name",
    "description": "Brief description",
    "strategy_type": "one of: momentum, mean_reversion, breakout, trend_following, scalping, dca, whale_following, sentiment, custom",
    "indicators": ["list of indicators to use"],
    "entry_conditions": [
        {{"indicator": "indicator_name", "operator": "> or < or == etc", "value": "number or indicator"}}
    ],
    "exit_conditions": [
        {{"indicator": "indicator_name", "operator": "operator", "value": "value"}}
    ],
    "risk_params": {{
        "stop_loss_pct": number (0-50),
        "take_profit_pct": number (0-200),
        "position_size_pct": number (1-100),
        "max_positions": number (1-20)
    }},
    "coins": ["list of coins to trade, or 'all' for all available"],
    "timeframe": "1h, 4h, 1d, or 1w",
    "notes": "any additional notes"
}}

Available indicators: {list(self.available_indicators.keys())}
Available operators: {self.operators}

Respond ONLY with the JSON object, no additional text."""

            # Get AI response
            response = await self.ai_chat.chat(
                query=prompt,
                session_id=session_id,
                include_market_data=False,
                include_news=False
            )
            
            # Parse the AI response
            ai_response = response.get('response', '')
            
            # Extract JSON from response
            strategy = self._parse_strategy_json(ai_response)
            
            if strategy:
                # Validate and enhance the strategy
                validated = self._validate_strategy(strategy)
                
                if validated['valid']:
                    # Store the strategy
                    strategy['created_at'] = datetime.now(timezone.utc)
                    strategy['created_by'] = 'ai_builder'
                    strategy['source_description'] = description
                    strategy['status'] = 'draft'
                    
                    result = await self.db.custom_strategies.insert_one(strategy)
                    strategy['_id'] = str(result.inserted_id)
                    
                    return {
                        'success': True,
                        'strategy': self._clean_strategy_for_response(strategy),
                        'validation': validated,
                        'message': 'Strategy created successfully from your description'
                    }
                else:
                    return {
                        'success': False,
                        'partial_strategy': strategy,
                        'validation': validated,
                        'message': 'Strategy parsed but has validation issues'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Could not parse strategy from AI response',
                    'ai_response': ai_response[:500]
                }
                
        except Exception as e:
            logger.error(f"Strategy building failed: {e}")
            return {'error': str(e)}
    
    def _parse_strategy_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        try:
            # Try direct JSON parse
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in the text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return None
    
    def _validate_strategy(self, strategy: Dict) -> Dict[str, Any]:
        """Validate strategy configuration"""
        issues = []
        warnings = []
        
        # Check required fields
        required = ['name', 'entry_conditions', 'exit_conditions']
        for field in required:
            if field not in strategy or not strategy[field]:
                issues.append(f"Missing required field: {field}")
        
        # Validate entry conditions
        if 'entry_conditions' in strategy:
            for i, cond in enumerate(strategy['entry_conditions']):
                if 'indicator' not in cond:
                    issues.append(f"Entry condition {i+1}: missing indicator")
                if 'operator' not in cond:
                    issues.append(f"Entry condition {i+1}: missing operator")
                if 'value' not in cond:
                    issues.append(f"Entry condition {i+1}: missing value")
        
        # Validate exit conditions
        if 'exit_conditions' in strategy:
            for i, cond in enumerate(strategy['exit_conditions']):
                if 'indicator' not in cond:
                    issues.append(f"Exit condition {i+1}: missing indicator")
        
        # Validate risk params
        risk = strategy.get('risk_params', {})
        if risk.get('stop_loss_pct', 0) > 50:
            warnings.append("Stop loss > 50% is very risky")
        if risk.get('position_size_pct', 0) > 50:
            warnings.append("Position size > 50% is very risky")
        if risk.get('take_profit_pct', 0) < risk.get('stop_loss_pct', 0):
            warnings.append("Take profit is less than stop loss - poor risk/reward ratio")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def _clean_strategy_for_response(self, strategy: Dict) -> Dict:
        """Remove MongoDB-specific fields for API response"""
        cleaned = {k: v for k, v in strategy.items() if k != '_id' or isinstance(v, str)}
        if 'created_at' in cleaned and hasattr(cleaned['created_at'], 'isoformat'):
            cleaned['created_at'] = cleaned['created_at'].isoformat()
        return cleaned
    
    async def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get a strategy template"""
        if template_name not in self.templates:
            return {
                'error': f"Template '{template_name}' not found",
                'available_templates': list(self.templates.keys())
            }
        
        template = self.templates[template_name].copy()
        template['template_name'] = template_name
        return template
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all available strategy templates"""
        return [
            {
                'name': key,
                'display_name': val['name'],
                'description': val['description'],
                'indicators': val['indicators']
            }
            for key, val in self.templates.items()
        ]
    
    async def create_from_template(self, template_name: str, customizations: Dict = None) -> Dict[str, Any]:
        """Create a new strategy from a template with optional customizations"""
        if template_name not in self.templates:
            return {'error': f"Template '{template_name}' not found"}
        
        # Copy template
        strategy = self.templates[template_name].copy()
        strategy['template_name'] = template_name
        
        # Apply customizations
        if customizations:
            if 'name' in customizations:
                strategy['name'] = customizations['name']
            if 'risk_params' in customizations:
                strategy['risk_params'].update(customizations['risk_params'])
            if 'coins' in customizations:
                strategy['coins'] = customizations['coins']
            if 'entry_conditions' in customizations:
                strategy['entry_conditions'] = customizations['entry_conditions']
            if 'exit_conditions' in customizations:
                strategy['exit_conditions'] = customizations['exit_conditions']
        
        # Validate
        validation = self._validate_strategy(strategy)
        
        # Store
        strategy['created_at'] = datetime.now(timezone.utc)
        strategy['created_by'] = 'template'
        strategy['status'] = 'draft'
        
        result = await self.db.custom_strategies.insert_one(strategy)
        strategy['_id'] = str(result.inserted_id)
        
        return {
            'success': True,
            'strategy': self._clean_strategy_for_response(strategy),
            'validation': validation
        }
    
    async def save_strategy(self, strategy: Dict) -> Dict[str, Any]:
        """Save a custom strategy"""
        validation = self._validate_strategy(strategy)
        
        if not validation['valid']:
            return {
                'success': False,
                'validation': validation,
                'message': 'Strategy has validation issues'
            }
        
        strategy['created_at'] = datetime.now(timezone.utc)
        strategy['updated_at'] = datetime.now(timezone.utc)
        strategy['status'] = strategy.get('status', 'draft')
        
        result = await self.db.custom_strategies.insert_one(strategy)
        strategy['_id'] = str(result.inserted_id)
        
        return {
            'success': True,
            'strategy': self._clean_strategy_for_response(strategy),
            'validation': validation
        }
    
    async def list_strategies(self, status: str = None) -> List[Dict]:
        """List all saved strategies"""
        query = {}
        if status:
            query['status'] = status
        
        cursor = self.db.custom_strategies.find(query, {'_id': 0}).sort('created_at', -1)
        strategies = await cursor.to_list(length=100)
        
        return strategies
    
    async def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """Get a specific strategy by ID"""
        from bson import ObjectId
        try:
            strategy = await self.db.custom_strategies.find_one(
                {'_id': ObjectId(strategy_id)},
                {'_id': 0}
            )
            return strategy
        except:
            return None
    
    async def activate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Activate a strategy for live/paper trading"""
        from bson import ObjectId
        try:
            result = await self.db.custom_strategies.update_one(
                {'_id': ObjectId(strategy_id)},
                {'$set': {'status': 'active', 'activated_at': datetime.now(timezone.utc)}}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Strategy activated'}
            return {'success': False, 'message': 'Strategy not found'}
        except Exception as e:
            return {'error': str(e)}
    
    async def deactivate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Deactivate a strategy"""
        from bson import ObjectId
        try:
            result = await self.db.custom_strategies.update_one(
                {'_id': ObjectId(strategy_id)},
                {'$set': {'status': 'inactive', 'deactivated_at': datetime.now(timezone.utc)}}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Strategy deactivated'}
            return {'success': False, 'message': 'Strategy not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_available_indicators(self) -> Dict[str, List[str]]:
        """Get all available indicators by category"""
        return self.available_indicators
    
    async def get_ai_suggestions(self, partial_strategy: Dict, session_id: str = "default") -> Dict[str, Any]:
        """Get AI suggestions to improve a strategy"""
        if not self.ai_chat:
            return {'error': 'AI chat service not available'}
        
        prompt = f"""Review this trading strategy and provide improvement suggestions:

Strategy:
{json.dumps(partial_strategy, indent=2)}

Please provide:
1. Potential improvements to entry/exit conditions
2. Risk management suggestions
3. Additional indicators that might help
4. Potential weaknesses to address
5. Market conditions where this strategy might perform poorly

Be specific and actionable in your suggestions."""

        response = await self.ai_chat.chat(
            query=prompt,
            session_id=session_id,
            include_market_data=False,
            include_news=False
        )
        
        return {
            'suggestions': response.get('response', ''),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Singleton
_strategy_builder = None

def get_strategy_builder(db: AsyncIOMotorDatabase = None, ai_chat=None) -> CustomStrategyBuilder:
    global _strategy_builder
    if _strategy_builder is None and db is not None:
        _strategy_builder = CustomStrategyBuilder(db, ai_chat)
    return _strategy_builder
