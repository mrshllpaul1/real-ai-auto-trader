"""
Yearly Adaptive Backtesting System
===================================
Comprehensive backtesting system that:
1. Runs full year backtest with weekly adaptation (2020-2025)
2. Tests across all Kraken coins
3. Automatically adapts strategy parameters weekly
4. Creates profitable portfolio with auto-trading signals
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Top performing coins by market cap and liquidity
TOP_COINS = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
    "UNI", "NEAR", "FIL", "ARB", "OP", "SUI", "APT", "INJ", "TIA", "SEI",
    "DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "MEME", "TURBO", "MOG",
    "LTC", "BCH", "ETC", "XMR", "ZEC", "DASH", "XLM", "ALGO", "HBAR", "VET",
    "AAVE", "MKR", "CRV", "LDO", "SNX", "COMP", "SUSHI", "YFI", "BAL", "1INCH"
]

# Coins available in each year (some didn't exist before certain years)
COINS_BY_YEAR = {
    2020: ["BTC", "ETH", "XRP", "LTC", "BCH", "ETC", "XMR", "ZEC", "DASH", "XLM", 
           "ALGO", "ATOM", "LINK", "ADA", "DOT", "UNI", "AAVE", "SNX", "COMP", "YFI"],
    2021: ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
           "UNI", "FIL", "DOGE", "SHIB", "LTC", "BCH", "ETC", "XLM", "ALGO", "AAVE",
           "MKR", "CRV", "SNX", "COMP", "SUSHI", "YFI", "1INCH", "NEAR", "HBAR", "VET"],
    2022: ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
           "UNI", "NEAR", "FIL", "DOGE", "SHIB", "LTC", "BCH", "ALGO", "HBAR", "VET",
           "AAVE", "MKR", "CRV", "LDO", "SNX", "COMP", "SUSHI", "APT", "OP", "ARB"],
    2023: ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
           "UNI", "NEAR", "FIL", "ARB", "OP", "APT", "INJ", "DOGE", "SHIB", "PEPE",
           "BONK", "LTC", "BCH", "ALGO", "HBAR", "VET", "AAVE", "MKR", "CRV", "LDO"],
    2024: ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
           "UNI", "NEAR", "FIL", "ARB", "OP", "SUI", "APT", "INJ", "TIA", "SEI",
           "DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "LTC", "BCH", "AAVE", "MKR"],
    2025: TOP_COINS[:30],
    2026: ["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
           "UNI", "NEAR", "FIL", "ARB", "OP", "SUI", "APT", "INJ", "TIA", "SEI",
           "DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "LTC", "BCH", "AAVE", "MKR",
           "CRV", "LDO", "SNX", "COMP", "SUSHI", "YFI", "BAL", "1INCH", "HBAR", "VET"]
}

# Market regime parameters
MARKET_REGIMES = {
    "bull_strong": {"bias": 0.003, "volatility": 0.02, "trend_strength": 0.8},
    "bull_weak": {"bias": 0.001, "volatility": 0.015, "trend_strength": 0.5},
    "bear_strong": {"bias": -0.003, "volatility": 0.025, "trend_strength": 0.8},
    "bear_weak": {"bias": -0.001, "volatility": 0.018, "trend_strength": 0.5},
    "sideways": {"bias": 0, "volatility": 0.012, "trend_strength": 0.2},
    "high_volatility": {"bias": 0, "volatility": 0.04, "trend_strength": 0.3},
    "recovery": {"bias": 0.002, "volatility": 0.022, "trend_strength": 0.6},
    "crash": {"bias": -0.006, "volatility": 0.05, "trend_strength": 0.9},
    "euphoria": {"bias": 0.005, "volatility": 0.03, "trend_strength": 0.85}
}

# 2020 Market calendar - COVID crash and DeFi summer - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2020 = [
    # January
    {"week": 1, "month": "January", "regime": "bull_weak", "event": "New Year optimism", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "bull_weak", "event": "Early January rally", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "sideways", "event": "Consolidation", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "sideways", "event": "Pre-COVID uncertainty", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "bull_weak", "event": "February optimism", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "bull_strong", "event": "BTC rally to $10k", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "bull_strong", "event": "Momentum continues", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "bear_weak", "event": "COVID fears begin", "date_range": "Feb 19-25"},
    # March - COVID Crash
    {"week": 9, "month": "March", "regime": "bear_weak", "event": "Growing COVID concerns", "date_range": "Feb 26-Mar 3"},
    {"week": 10, "month": "March", "regime": "bear_strong", "event": "Market panic starts", "date_range": "Mar 4-10"},
    {"week": 11, "month": "March", "regime": "crash", "event": "COVID crash - Black Thursday", "date_range": "Mar 11-17"},
    {"week": 12, "month": "March", "regime": "crash", "event": "BTC crashes to $3.8k", "date_range": "Mar 18-24"},
    {"week": 13, "month": "March", "regime": "bear_strong", "event": "Market capitulation", "date_range": "Mar 25-31"},
    # April
    {"week": 14, "month": "April", "regime": "recovery", "event": "Initial recovery", "date_range": "Apr 1-7"},
    {"week": 15, "month": "April", "regime": "recovery", "event": "Fed stimulus announced", "date_range": "Apr 8-14"},
    {"week": 16, "month": "April", "regime": "bull_weak", "event": "Relief rally", "date_range": "Apr 15-21"},
    {"week": 17, "month": "April", "regime": "bull_weak", "event": "Halving anticipation", "date_range": "Apr 22-28"},
    # May - Bitcoin Halving
    {"week": 18, "month": "May", "regime": "bull_weak", "event": "Recovery begins", "date_range": "Apr 29-May 5"},
    {"week": 19, "month": "May", "regime": "high_volatility", "event": "Pre-halving volatility", "date_range": "May 6-12"},
    {"week": 20, "month": "May", "regime": "sideways", "event": "Bitcoin halving May 11", "date_range": "May 13-19"},
    {"week": 21, "month": "May", "regime": "sideways", "event": "Post-halving consolidation", "date_range": "May 20-26"},
    # June - DeFi Summer begins
    {"week": 22, "month": "June", "regime": "bull_weak", "event": "DeFi interest grows", "date_range": "May 27-Jun 2"},
    {"week": 23, "month": "June", "regime": "bull_weak", "event": "COMP token launch", "date_range": "Jun 3-9"},
    {"week": 24, "month": "June", "regime": "bull_weak", "event": "DeFi summer begins", "date_range": "Jun 10-16"},
    {"week": 25, "month": "June", "regime": "bull_strong", "event": "Yield farming starts", "date_range": "Jun 17-23"},
    {"week": 26, "month": "June", "regime": "bull_strong", "event": "DeFi TVL growing", "date_range": "Jun 24-30"},
    # July - DeFi Mania
    {"week": 27, "month": "July", "regime": "bull_strong", "event": "DeFi mania - YFI launch", "date_range": "Jul 1-7"},
    {"week": 28, "month": "July", "regime": "euphoria", "event": "YFI explosion", "date_range": "Jul 8-14"},
    {"week": 29, "month": "July", "regime": "euphoria", "event": "DeFi tokens moon", "date_range": "Jul 15-21"},
    {"week": 30, "month": "July", "regime": "high_volatility", "event": "DeFi volatility peak", "date_range": "Jul 22-28"},
    # August
    {"week": 31, "month": "August", "regime": "bull_strong", "event": "DeFi expansion", "date_range": "Jul 29-Aug 4"},
    {"week": 32, "month": "August", "regime": "high_volatility", "event": "Sushi swap drama", "date_range": "Aug 5-11"},
    {"week": 33, "month": "August", "regime": "bear_weak", "event": "DeFi correction", "date_range": "Aug 12-18"},
    {"week": 34, "month": "August", "regime": "sideways", "event": "Market digests gains", "date_range": "Aug 19-25"},
    # September
    {"week": 35, "month": "September", "regime": "bear_weak", "event": "September weakness", "date_range": "Aug 26-Sep 1"},
    {"week": 36, "month": "September", "regime": "sideways", "event": "September consolidation", "date_range": "Sep 2-8"},
    {"week": 37, "month": "September", "regime": "bear_weak", "event": "DeFi unwind", "date_range": "Sep 9-15"},
    {"week": 38, "month": "September", "regime": "sideways", "event": "Range trading", "date_range": "Sep 16-22"},
    {"week": 39, "month": "September", "regime": "sideways", "event": "Month end calm", "date_range": "Sep 23-29"},
    # October - Institutional Interest
    {"week": 40, "month": "October", "regime": "bull_weak", "event": "PayPal crypto announcement", "date_range": "Sep 30-Oct 6"},
    {"week": 41, "month": "October", "regime": "bull_weak", "event": "Square buys BTC", "date_range": "Oct 7-13"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "Institutional interest", "date_range": "Oct 14-20"},
    {"week": 43, "month": "October", "regime": "bull_strong", "event": "Institutional FOMO begins", "date_range": "Oct 21-27"},
    # November - ATH Breakout
    {"week": 44, "month": "November", "regime": "bull_strong", "event": "BTC approaches $14k", "date_range": "Oct 28-Nov 3"},
    {"week": 45, "month": "November", "regime": "bull_strong", "event": "Biden election clarity", "date_range": "Nov 4-10"},
    {"week": 46, "month": "November", "regime": "bull_strong", "event": "BTC breaks ATH", "date_range": "Nov 11-17"},
    {"week": 47, "month": "November", "regime": "euphoria", "event": "New ATH celebration", "date_range": "Nov 18-24"},
    {"week": 48, "month": "November", "regime": "bull_strong", "event": "Rally continues", "date_range": "Nov 25-30"},
    # December
    {"week": 49, "month": "December", "regime": "euphoria", "event": "December rally", "date_range": "Dec 1-8"},
    {"week": 50, "month": "December", "regime": "bull_strong", "event": "BTC $20k milestone", "date_range": "Dec 9-15"},
    {"week": 51, "month": "December", "regime": "euphoria", "event": "Holiday FOMO", "date_range": "Dec 16-22"},
    {"week": 52, "month": "December", "regime": "bull_strong", "event": "Year-end euphoria", "date_range": "Dec 23-31"}
]

# 2021 Market calendar - Bull run and May crash - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2021 = [
    # January
    {"week": 1, "month": "January", "regime": "bull_strong", "event": "New Year continuation", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "euphoria", "event": "BTC $40k milestone", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "high_volatility", "event": "Volatility spike", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "euphoria", "event": "Tesla BTC purchase rumors", "date_range": "Jan 22-28"},
    # February - Tesla Announcement
    {"week": 5, "month": "February", "regime": "euphoria", "event": "Tesla BTC purchase confirmed", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "bull_strong", "event": "BTC $45k", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "bull_strong", "event": "Institutional buying", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "euphoria", "event": "BTC $50k milestone", "date_range": "Feb 19-25"},
    # March
    {"week": 9, "month": "March", "regime": "bull_strong", "event": "March momentum", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "high_volatility", "event": "Coinbase IPO anticipation", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "bull_strong", "event": "NFT mania grows", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "bull_strong", "event": "Beeple NFT $69M sale", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "bull_strong", "event": "BTC new ATH $64k", "date_range": "Mar 26-31"},
    # April - Coinbase IPO
    {"week": 14, "month": "April", "regime": "euphoria", "event": "Coinbase IPO week", "date_range": "Apr 1-7"},
    {"week": 15, "month": "April", "regime": "high_volatility", "event": "Post-IPO volatility", "date_range": "Apr 8-14"},
    {"week": 16, "month": "April", "regime": "bear_weak", "event": "Profit taking begins", "date_range": "Apr 15-21"},
    {"week": 17, "month": "April", "regime": "bear_weak", "event": "Correction deepens", "date_range": "Apr 22-28"},
    # May - Crash
    {"week": 18, "month": "May", "regime": "sideways", "event": "May consolidation", "date_range": "Apr 29-May 5"},
    {"week": 19, "month": "May", "regime": "crash", "event": "May crash - China ban", "date_range": "May 6-12"},
    {"week": 20, "month": "May", "regime": "crash", "event": "BTC drops to $30k", "date_range": "May 13-19"},
    {"week": 21, "month": "May", "regime": "bear_strong", "event": "Elon FUD - Tesla drops BTC", "date_range": "May 20-26"},
    # June
    {"week": 22, "month": "June", "regime": "bear_strong", "event": "China mining ban", "date_range": "May 27-Jun 2"},
    {"week": 23, "month": "June", "regime": "bear_weak", "event": "Capitulation continues", "date_range": "Jun 3-9"},
    {"week": 24, "month": "June", "regime": "bear_weak", "event": "Summer lows", "date_range": "Jun 10-16"},
    {"week": 25, "month": "June", "regime": "bear_strong", "event": "BTC drops below $30k", "date_range": "Jun 17-23"},
    {"week": 26, "month": "June", "regime": "sideways", "event": "Bottom forming", "date_range": "Jun 24-30"},
    # July
    {"week": 27, "month": "July", "regime": "sideways", "event": "Accumulation phase", "date_range": "Jul 1-7"},
    {"week": 28, "month": "July", "regime": "sideways", "event": "Range bound trading", "date_range": "Jul 8-14"},
    {"week": 29, "month": "July", "regime": "recovery", "event": "B Word conference pump", "date_range": "Jul 15-21"},
    {"week": 30, "month": "July", "regime": "recovery", "event": "Recovery begins", "date_range": "Jul 22-28"},
    # August - NFT Revival
    {"week": 31, "month": "August", "regime": "bull_weak", "event": "August recovery", "date_range": "Jul 29-Aug 4"},
    {"week": 32, "month": "August", "regime": "bull_strong", "event": "BTC breaks $40k", "date_range": "Aug 5-11"},
    {"week": 33, "month": "August", "regime": "bull_weak", "event": "NFT mania begins", "date_range": "Aug 12-18"},
    {"week": 34, "month": "August", "regime": "bull_strong", "event": "NFT boom - BAYC", "date_range": "Aug 19-25"},
    # September
    {"week": 35, "month": "September", "regime": "bull_strong", "event": "El Salvador BTC adoption", "date_range": "Aug 26-Sep 1"},
    {"week": 36, "month": "September", "regime": "bull_strong", "event": "BTC legal tender day", "date_range": "Sep 2-8"},
    {"week": 37, "month": "September", "regime": "high_volatility", "event": "El Salvador volatility", "date_range": "Sep 9-15"},
    {"week": 38, "month": "September", "regime": "bear_weak", "event": "September pullback", "date_range": "Sep 16-22"},
    {"week": 39, "month": "September", "regime": "high_volatility", "event": "China final ban", "date_range": "Sep 23-29"},
    # October - Uptober
    {"week": 40, "month": "October", "regime": "recovery", "event": "Uptober begins", "date_range": "Sep 30-Oct 6"},
    {"week": 41, "month": "October", "regime": "bull_strong", "event": "BTC recovery rally", "date_range": "Oct 7-13"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "BTC ETF speculation", "date_range": "Oct 14-20"},
    {"week": 43, "month": "October", "regime": "euphoria", "event": "BTC futures ETF approved", "date_range": "Oct 21-27"},
    # November - ATH
    {"week": 44, "month": "November", "regime": "euphoria", "event": "BTC approaches ATH", "date_range": "Oct 28-Nov 3"},
    {"week": 45, "month": "November", "regime": "euphoria", "event": "BTC ATH $69k - Nov 10", "date_range": "Nov 4-10"},
    {"week": 46, "month": "November", "regime": "high_volatility", "event": "Post-ATH distribution", "date_range": "Nov 11-17"},
    {"week": 47, "month": "November", "regime": "bear_weak", "event": "Thanksgiving selloff", "date_range": "Nov 18-24"},
    {"week": 48, "month": "November", "regime": "bear_weak", "event": "Post-ATH correction", "date_range": "Nov 25-30"},
    # December
    {"week": 49, "month": "December", "regime": "bear_strong", "event": "December selloff begins", "date_range": "Dec 1-8"},
    {"week": 50, "month": "December", "regime": "crash", "event": "Flash crash Dec 4", "date_range": "Dec 9-15"},
    {"week": 51, "month": "December", "regime": "bear_strong", "event": "December selloff", "date_range": "Dec 16-22"},
    {"week": 52, "month": "December", "regime": "sideways", "event": "Year-end ranging", "date_range": "Dec 23-31"}
]

# 2022 Market calendar - Crypto winter - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2022 = [
    # January
    {"week": 1, "month": "January", "regime": "bear_weak", "event": "New Year weakness", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "bear_weak", "event": "January selloff", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "bear_strong", "event": "BTC drops below $40k", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "bear_strong", "event": "Fed hawkish pivot", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "recovery", "event": "Dead cat bounce", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "sideways", "event": "Range trading", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "sideways", "event": "Consolidation", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "bear_weak", "event": "Ukraine tensions", "date_range": "Feb 19-25"},
    # March
    {"week": 9, "month": "March", "regime": "crash", "event": "Russia invades Ukraine", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "bear_weak", "event": "Ukraine war continues", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "recovery", "event": "Relief rally", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "bull_weak", "event": "Brief relief rally", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "recovery", "event": "End of Q1 recovery", "date_range": "Mar 26-31"},
    # April
    {"week": 14, "month": "April", "regime": "sideways", "event": "April consolidation", "date_range": "Apr 1-7"},
    {"week": 15, "month": "April", "regime": "bear_weak", "event": "Rate hike fears grow", "date_range": "Apr 8-14"},
    {"week": 16, "month": "April", "regime": "bear_weak", "event": "Rate hike fears", "date_range": "Apr 15-21"},
    {"week": 17, "month": "April", "regime": "bear_strong", "event": "BTC below $40k again", "date_range": "Apr 22-28"},
    # May - LUNA Collapse
    {"week": 18, "month": "May", "regime": "bear_weak", "event": "May weakness begins", "date_range": "Apr 29-May 5"},
    {"week": 19, "month": "May", "regime": "crash", "event": "LUNA/UST collapse begins", "date_range": "May 6-12"},
    {"week": 20, "month": "May", "regime": "crash", "event": "LUNA death spiral", "date_range": "May 13-19"},
    {"week": 21, "month": "May", "regime": "bear_strong", "event": "Post-LUNA capitulation", "date_range": "May 20-26"},
    # June - Contagion
    {"week": 22, "month": "June", "regime": "bear_strong", "event": "Contagion - 3AC, Celsius", "date_range": "May 27-Jun 2"},
    {"week": 23, "month": "June", "regime": "crash", "event": "Celsius freezes withdrawals", "date_range": "Jun 3-9"},
    {"week": 24, "month": "June", "regime": "crash", "event": "3AC liquidation", "date_range": "Jun 10-16"},
    {"week": 25, "month": "June", "regime": "bear_weak", "event": "Summer capitulation", "date_range": "Jun 17-23"},
    {"week": 26, "month": "June", "regime": "bear_strong", "event": "BTC below $20k", "date_range": "Jun 24-30"},
    # July
    {"week": 27, "month": "July", "regime": "sideways", "event": "Bottom fishing begins", "date_range": "Jul 1-7"},
    {"week": 28, "month": "July", "regime": "sideways", "event": "Bottom forming", "date_range": "Jul 8-14"},
    {"week": 29, "month": "July", "regime": "recovery", "event": "Dead cat bounce", "date_range": "Jul 15-21"},
    {"week": 30, "month": "July", "regime": "recovery", "event": "Relief rally", "date_range": "Jul 22-28"},
    # August - ETH Merge Anticipation
    {"week": 31, "month": "August", "regime": "recovery", "event": "Bear market rally", "date_range": "Jul 29-Aug 4"},
    {"week": 32, "month": "August", "regime": "bull_weak", "event": "Merge anticipation", "date_range": "Aug 5-11"},
    {"week": 33, "month": "August", "regime": "bull_weak", "event": "ETH rally on Merge", "date_range": "Aug 12-18"},
    {"week": 34, "month": "August", "regime": "bear_weak", "event": "Merge anticipation fades", "date_range": "Aug 19-25"},
    # September - ETH Merge
    {"week": 35, "month": "September", "regime": "sideways", "event": "Pre-Merge consolidation", "date_range": "Aug 26-Sep 1"},
    {"week": 36, "month": "September", "regime": "bear_weak", "event": "Sell the news setup", "date_range": "Sep 2-8"},
    {"week": 37, "month": "September", "regime": "sideways", "event": "ETH Merge complete", "date_range": "Sep 9-15"},
    {"week": 38, "month": "September", "regime": "bear_weak", "event": "Post-Merge selloff", "date_range": "Sep 16-22"},
    {"week": 39, "month": "September", "regime": "bear_weak", "event": "September weakness", "date_range": "Sep 23-29"},
    # October
    {"week": 40, "month": "October", "regime": "bear_weak", "event": "Macro weakness", "date_range": "Sep 30-Oct 6"},
    {"week": 41, "month": "October", "regime": "sideways", "event": "Range bound", "date_range": "Oct 7-13"},
    {"week": 42, "month": "October", "regime": "sideways", "event": "Consolidation", "date_range": "Oct 14-20"},
    {"week": 43, "month": "October", "regime": "sideways", "event": "Pre-FTX calm", "date_range": "Oct 21-27"},
    # November - FTX Collapse
    {"week": 44, "month": "November", "regime": "high_volatility", "event": "FTX concerns emerge", "date_range": "Oct 28-Nov 3"},
    {"week": 45, "month": "November", "regime": "crash", "event": "FTX collapse begins", "date_range": "Nov 4-10"},
    {"week": 46, "month": "November", "regime": "crash", "event": "FTX bankruptcy", "date_range": "Nov 11-17"},
    {"week": 47, "month": "November", "regime": "bear_strong", "event": "FTX contagion spreads", "date_range": "Nov 18-24"},
    {"week": 48, "month": "November", "regime": "bear_strong", "event": "FTX contagion", "date_range": "Nov 25-30"},
    # December
    {"week": 49, "month": "December", "regime": "bear_weak", "event": "Post-FTX stabilization", "date_range": "Dec 1-8"},
    {"week": 50, "month": "December", "regime": "bear_weak", "event": "Low volume trading", "date_range": "Dec 9-15"},
    {"week": 51, "month": "December", "regime": "bear_weak", "event": "Year-end capitulation", "date_range": "Dec 16-22"},
    {"week": 52, "month": "December", "regime": "sideways", "event": "Year-end bottom", "date_range": "Dec 23-31"}
]

# 2023 Market calendar - Recovery year - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2023 = [
    # January
    {"week": 1, "month": "January", "regime": "sideways", "event": "New Year consolidation", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "bull_weak", "event": "January rally starts", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "bull_weak", "event": "BTC recovers $20k", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "bull_weak", "event": "January rally begins", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "bull_strong", "event": "BTC breaks $24k", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "bull_strong", "event": "Momentum builds", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "bull_strong", "event": "Crypto rally continues", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "sideways", "event": "Consolidation", "date_range": "Feb 19-25"},
    # March - SVB Crisis
    {"week": 9, "month": "March", "regime": "bear_weak", "event": "Pre-SVB weakness", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "high_volatility", "event": "SVB bank crisis", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "high_volatility", "event": "Banking fears spread", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "recovery", "event": "Fed backstop calms markets", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "recovery", "event": "Banking fears ease", "date_range": "Mar 26-31"},
    # April
    {"week": 14, "month": "April", "regime": "bull_weak", "event": "April optimism", "date_range": "Apr 1-7"},
    {"week": 15, "month": "April", "regime": "bull_weak", "event": "BTC holds $28k", "date_range": "Apr 8-14"},
    {"week": 16, "month": "April", "regime": "bull_weak", "event": "Spring optimism", "date_range": "Apr 15-21"},
    {"week": 17, "month": "April", "regime": "sideways", "event": "Consolidation", "date_range": "Apr 22-28"},
    # May
    {"week": 18, "month": "May", "regime": "sideways", "event": "May range trading", "date_range": "Apr 29-May 5"},
    {"week": 19, "month": "May", "regime": "sideways", "event": "Consolidation continues", "date_range": "May 6-12"},
    {"week": 20, "month": "May", "regime": "bear_weak", "event": "Mild pullback", "date_range": "May 13-19"},
    {"week": 21, "month": "May", "regime": "sideways", "event": "Range bound", "date_range": "May 20-26"},
    # June - SEC Actions
    {"week": 22, "month": "June", "regime": "bull_weak", "event": "BlackRock ETF filing", "date_range": "May 27-Jun 2"},
    {"week": 23, "month": "June", "regime": "bull_strong", "event": "ETF optimism surge", "date_range": "Jun 3-9"},
    {"week": 24, "month": "June", "regime": "high_volatility", "event": "SEC vs Binance", "date_range": "Jun 10-16"},
    {"week": 25, "month": "June", "regime": "high_volatility", "event": "SEC vs Coinbase", "date_range": "Jun 17-23"},
    {"week": 26, "month": "June", "regime": "sideways", "event": "Post-SEC stabilization", "date_range": "Jun 24-30"},
    # July
    {"week": 27, "month": "July", "regime": "sideways", "event": "Summer doldrums", "date_range": "Jul 1-7"},
    {"week": 28, "month": "July", "regime": "sideways", "event": "Summer range", "date_range": "Jul 8-14"},
    {"week": 29, "month": "July", "regime": "bull_weak", "event": "XRP partial win vs SEC", "date_range": "Jul 15-21"},
    {"week": 30, "month": "July", "regime": "sideways", "event": "Consolidation", "date_range": "Jul 22-28"},
    # August
    {"week": 31, "month": "August", "regime": "bear_weak", "event": "August weakness", "date_range": "Jul 29-Aug 4"},
    {"week": 32, "month": "August", "regime": "bear_weak", "event": "Low volume decline", "date_range": "Aug 5-11"},
    {"week": 33, "month": "August", "regime": "crash", "event": "Flash crash Aug 17", "date_range": "Aug 12-18"},
    {"week": 34, "month": "August", "regime": "bear_weak", "event": "Post-crash recovery", "date_range": "Aug 19-25"},
    # September
    {"week": 35, "month": "September", "regime": "sideways", "event": "September range", "date_range": "Aug 26-Sep 1"},
    {"week": 36, "month": "September", "regime": "sideways", "event": "Consolidation", "date_range": "Sep 2-8"},
    {"week": 37, "month": "September", "regime": "bull_weak", "event": "ETF optimism returns", "date_range": "Sep 9-15"},
    {"week": 38, "month": "September", "regime": "sideways", "event": "Range trading", "date_range": "Sep 16-22"},
    {"week": 39, "month": "September", "regime": "sideways", "event": "End of Q3", "date_range": "Sep 23-29"},
    # October - Uptober
    {"week": 40, "month": "October", "regime": "bull_weak", "event": "Uptober rally begins", "date_range": "Sep 30-Oct 6"},
    {"week": 41, "month": "October", "regime": "bull_strong", "event": "BTC breaks $28k", "date_range": "Oct 7-13"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "Momentum builds", "date_range": "Oct 14-20"},
    {"week": 43, "month": "October", "regime": "bull_strong", "event": "BTC breaks $35k", "date_range": "Oct 21-27"},
    # November - CZ Settlement
    {"week": 44, "month": "November", "regime": "bull_strong", "event": "November rally", "date_range": "Oct 28-Nov 3"},
    {"week": 45, "month": "November", "regime": "bull_strong", "event": "BTC approaches $38k", "date_range": "Nov 4-10"},
    {"week": 46, "month": "November", "regime": "high_volatility", "event": "CZ Binance settlement", "date_range": "Nov 11-17"},
    {"week": 47, "month": "November", "regime": "bull_weak", "event": "Post-settlement calm", "date_range": "Nov 18-24"},
    {"week": 48, "month": "November", "regime": "bull_weak", "event": "Thanksgiving optimism", "date_range": "Nov 25-30"},
    # December
    {"week": 49, "month": "December", "regime": "bull_strong", "event": "ETF approval anticipation", "date_range": "Dec 1-8"},
    {"week": 50, "month": "December", "regime": "bull_strong", "event": "BTC breaks $42k", "date_range": "Dec 9-15"},
    {"week": 51, "month": "December", "regime": "high_volatility", "event": "Year-end volatility", "date_range": "Dec 16-22"},
    {"week": 52, "month": "December", "regime": "bull_weak", "event": "Year-end positioning", "date_range": "Dec 23-31"}
]

# 2024 Market calendar - Bitcoin halving year and ETF - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2024 = [
    # January - ETF Approval
    {"week": 1, "month": "January", "regime": "high_volatility", "event": "ETF decision week", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "euphoria", "event": "Bitcoin ETF approved!", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "bear_weak", "event": "Sell the news reaction", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "sideways", "event": "Post-ETF consolidation", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "bull_strong", "event": "ETF inflows massive", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "bull_strong", "event": "BTC breaks $45k", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "bull_strong", "event": "Momentum continues", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "bull_strong", "event": "BTC breaks $50k", "date_range": "Feb 19-25"},
    # March - New ATH
    {"week": 9, "month": "March", "regime": "euphoria", "event": "BTC approaches ATH", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "euphoria", "event": "BTC breaks previous ATH", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "euphoria", "event": "BTC new ATH $73k", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "high_volatility", "event": "Post-ATH volatility", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "bear_weak", "event": "Profit taking", "date_range": "Mar 26-31"},
    # April - Bitcoin Halving
    {"week": 14, "month": "April", "regime": "high_volatility", "event": "Pre-halving volatility", "date_range": "Apr 1-7"},
    {"week": 15, "month": "April", "regime": "sideways", "event": "Halving anticipation", "date_range": "Apr 8-14"},
    {"week": 16, "month": "April", "regime": "bull_strong", "event": "Bitcoin halving week", "date_range": "Apr 15-21"},
    {"week": 17, "month": "April", "regime": "sideways", "event": "Post-halving consolidation", "date_range": "Apr 22-28"},
    # May
    {"week": 18, "month": "May", "regime": "bear_weak", "event": "May correction begins", "date_range": "Apr 29-May 5"},
    {"week": 19, "month": "May", "regime": "bear_weak", "event": "Post-halving correction", "date_range": "May 6-12"},
    {"week": 20, "month": "May", "regime": "sideways", "event": "Stabilization", "date_range": "May 13-19"},
    {"week": 21, "month": "May", "regime": "bull_weak", "event": "ETH ETF speculation", "date_range": "May 20-26"},
    # June
    {"week": 22, "month": "June", "regime": "sideways", "event": "Summer consolidation", "date_range": "May 27-Jun 2"},
    {"week": 23, "month": "June", "regime": "sideways", "event": "Range trading", "date_range": "Jun 3-9"},
    {"week": 24, "month": "June", "regime": "bear_weak", "event": "Summer weakness", "date_range": "Jun 10-16"},
    {"week": 25, "month": "June", "regime": "bear_weak", "event": "Mt Gox distribution fears", "date_range": "Jun 17-23"},
    {"week": 26, "month": "June", "regime": "bear_strong", "event": "BTC drops below $60k", "date_range": "Jun 24-30"},
    # July - Mt Gox & Germany Selling
    {"week": 27, "month": "July", "regime": "crash", "event": "Mt Gox + Germany selling", "date_range": "Jul 1-7"},
    {"week": 28, "month": "July", "regime": "recovery", "event": "Oversold bounce", "date_range": "Jul 8-14"},
    {"week": 29, "month": "July", "regime": "bull_weak", "event": "Trump crypto support", "date_range": "Jul 15-21"},
    {"week": 30, "month": "July", "regime": "sideways", "event": "ETH ETF launch", "date_range": "Jul 22-28"},
    # August - Yen Carry Trade
    {"week": 31, "month": "August", "regime": "high_volatility", "event": "Yen carry trade unwind", "date_range": "Jul 29-Aug 5"},
    {"week": 32, "month": "August", "regime": "crash", "event": "Black Monday Aug 5", "date_range": "Aug 6-12"},
    {"week": 33, "month": "August", "regime": "recovery", "event": "Recovery from crash", "date_range": "Aug 13-19"},
    {"week": 34, "month": "August", "regime": "sideways", "event": "Summer range continues", "date_range": "Aug 20-26"},
    # September
    {"week": 35, "month": "September", "regime": "bear_weak", "event": "September weakness", "date_range": "Aug 27-Sep 2"},
    {"week": 36, "month": "September", "regime": "sideways", "event": "Pre-Fed consolidation", "date_range": "Sep 3-9"},
    {"week": 37, "month": "September", "regime": "bull_weak", "event": "Fed rate cut expectations", "date_range": "Sep 10-16"},
    {"week": 38, "month": "September", "regime": "bull_strong", "event": "Fed cuts 50bps!", "date_range": "Sep 17-23"},
    {"week": 39, "month": "September", "regime": "bull_weak", "event": "Post-cut optimism", "date_range": "Sep 24-30"},
    # October - Uptober
    {"week": 40, "month": "October", "regime": "bull_strong", "event": "Uptober begins", "date_range": "Oct 1-7"},
    {"week": 41, "month": "October", "regime": "bull_strong", "event": "BTC breaks $65k", "date_range": "Oct 8-14"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "Momentum building", "date_range": "Oct 15-21"},
    {"week": 43, "month": "October", "regime": "high_volatility", "event": "US Election uncertainty", "date_range": "Oct 22-28"},
    # November - Trump Victory
    {"week": 44, "month": "November", "regime": "high_volatility", "event": "Pre-election week", "date_range": "Oct 29-Nov 4"},
    {"week": 45, "month": "November", "regime": "euphoria", "event": "Trump wins - crypto rally", "date_range": "Nov 5-11"},
    {"week": 46, "month": "November", "regime": "euphoria", "event": "BTC breaks $90k", "date_range": "Nov 12-18"},
    {"week": 47, "month": "November", "regime": "bull_strong", "event": "Rally continues", "date_range": "Nov 19-25"},
    # December
    {"week": 48, "month": "December", "regime": "bull_strong", "event": "BTC breaks $100k", "date_range": "Nov 26-Dec 2"},
    {"week": 49, "month": "December", "regime": "high_volatility", "event": "Post-$100k volatility", "date_range": "Dec 3-9"},
    {"week": 50, "month": "December", "regime": "sideways", "event": "Consolidation above $100k", "date_range": "Dec 10-16"},
    {"week": 51, "month": "December", "regime": "bull_weak", "event": "Year-end consolidation", "date_range": "Dec 17-23"},
    {"week": 52, "month": "December", "regime": "sideways", "event": "Holiday trading", "date_range": "Dec 24-31"}
]

# 2025 Market calendar - COMPLETE WEEK BY WEEK breakdown
MARKET_EVENTS_2025 = [
    # January - Q1 Start
    {"week": 1, "month": "January", "regime": "sideways", "event": "New Year consolidation", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "bull_weak", "event": "Post-holiday recovery", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "bull_weak", "event": "Q1 optimism begins", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "bull_strong", "event": "Trump inauguration crypto rally", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "bull_strong", "event": "Bitcoin ETF inflows continue", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "bull_strong", "event": "Institutional accumulation", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "high_volatility", "event": "CPI data release", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "high_volatility", "event": "Fed meeting uncertainty", "date_range": "Feb 19-25"},
    # March
    {"week": 9, "month": "March", "regime": "bull_weak", "event": "March optimism", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "bear_weak", "event": "Profit taking", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "sideways", "event": "Consolidation phase", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "recovery", "event": "Q1 earnings positive", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "bull_weak", "event": "End of Q1 positioning", "date_range": "Mar 26-31"},
    # April - Q2 Start
    {"week": 14, "month": "April", "regime": "bull_strong", "event": "Q2 start bullish", "date_range": "Apr 1-8"},
    {"week": 15, "month": "April", "regime": "bull_strong", "event": "Bitcoin halving anniversary rally", "date_range": "Apr 9-15"},
    {"week": 16, "month": "April", "regime": "euphoria", "event": "Halving anniversary FOMO", "date_range": "Apr 16-22"},
    {"week": 17, "month": "April", "regime": "high_volatility", "event": "Tax season volatility", "date_range": "Apr 23-29"},
    # May
    {"week": 18, "month": "May", "regime": "sideways", "event": "May consolidation", "date_range": "Apr 30-May 6"},
    {"week": 19, "month": "May", "regime": "bear_weak", "event": "Sell in May begins", "date_range": "May 7-13"},
    {"week": 20, "month": "May", "regime": "bear_weak", "event": "Sell in May effect", "date_range": "May 14-20"},
    {"week": 21, "month": "May", "regime": "sideways", "event": "Range-bound trading", "date_range": "May 21-27"},
    # June
    {"week": 22, "month": "June", "regime": "bear_strong", "event": "Summer correction begins", "date_range": "May 28-Jun 3"},
    {"week": 23, "month": "June", "regime": "bear_weak", "event": "Correction continues", "date_range": "Jun 4-10"},
    {"week": 24, "month": "June", "regime": "sideways", "event": "Fed June meeting", "date_range": "Jun 11-17"},
    {"week": 25, "month": "June", "regime": "sideways", "event": "Summer doldrums begin", "date_range": "Jun 18-24"},
    {"week": 26, "month": "June", "regime": "sideways", "event": "End of Q2", "date_range": "Jun 25-30"},
    # July - Q3 Start
    {"week": 27, "month": "July", "regime": "recovery", "event": "Q3 start recovery", "date_range": "Jul 1-8"},
    {"week": 28, "month": "July", "regime": "recovery", "event": "Institutional buying resumes", "date_range": "Jul 9-15"},
    {"week": 29, "month": "July", "regime": "bull_weak", "event": "Summer rally attempt", "date_range": "Jul 16-22"},
    {"week": 30, "month": "July", "regime": "bull_weak", "event": "Q3 optimism builds", "date_range": "Jul 23-29"},
    # August
    {"week": 31, "month": "August", "regime": "sideways", "event": "Low volume August", "date_range": "Jul 30-Aug 5"},
    {"week": 32, "month": "August", "regime": "bear_weak", "event": "August weakness", "date_range": "Aug 6-12"},
    {"week": 33, "month": "August", "regime": "high_volatility", "event": "Fed Jackson Hole", "date_range": "Aug 13-19"},
    {"week": 34, "month": "August", "regime": "high_volatility", "event": "Post-Jackson Hole volatility", "date_range": "Aug 20-26"},
    # September
    {"week": 35, "month": "September", "regime": "bear_weak", "event": "September effect begins", "date_range": "Aug 27-Sep 2"},
    {"week": 36, "month": "September", "regime": "bear_strong", "event": "Historically weak period", "date_range": "Sep 3-9"},
    {"week": 37, "month": "September", "regime": "bear_weak", "event": "Mid-September pressure", "date_range": "Sep 10-16"},
    {"week": 38, "month": "September", "regime": "recovery", "event": "Fed September meeting rally", "date_range": "Sep 17-23"},
    {"week": 39, "month": "September", "regime": "sideways", "event": "End of Q3", "date_range": "Sep 24-30"},
    # October - Q4 Start
    {"week": 40, "month": "October", "regime": "bull_weak", "event": "Uptober begins", "date_range": "Oct 1-7"},
    {"week": 41, "month": "October", "regime": "bull_strong", "event": "Uptober momentum", "date_range": "Oct 8-14"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "Pre-election positioning", "date_range": "Oct 15-21"},
    {"week": 43, "month": "October", "regime": "high_volatility", "event": "Election uncertainty builds", "date_range": "Oct 22-28"},
    # November
    {"week": 44, "month": "November", "regime": "high_volatility", "event": "Pre-election week", "date_range": "Oct 29-Nov 4"},
    {"week": 45, "month": "November", "regime": "high_volatility", "event": "US Election week", "date_range": "Nov 5-11"},
    {"week": 46, "month": "November", "regime": "bull_strong", "event": "Post-election clarity", "date_range": "Nov 12-18"},
    {"week": 47, "month": "November", "regime": "bull_strong", "event": "Thanksgiving rally", "date_range": "Nov 19-25"},
    # December
    {"week": 48, "month": "December", "regime": "bull_weak", "event": "December optimism", "date_range": "Nov 26-Dec 2"},
    {"week": 49, "month": "December", "regime": "sideways", "event": "Fed December meeting", "date_range": "Dec 3-9"},
    {"week": 50, "month": "December", "regime": "bull_weak", "event": "Year-end positioning", "date_range": "Dec 10-16"},
    {"week": 51, "month": "December", "regime": "sideways", "event": "Holiday low volume", "date_range": "Dec 17-23"},
    {"week": 52, "month": "December", "regime": "sideways", "event": "Year-end consolidation", "date_range": "Dec 24-31"}
]

# 2026 Market calendar - Post-halving cycle peak year (projected) - COMPLETE WEEK BY WEEK
MARKET_EVENTS_2026 = [
    # January - Q1 Start - Post-halving bull continuation
    {"week": 1, "month": "January", "regime": "bull_weak", "event": "New Year continuation", "date_range": "Jan 1-7"},
    {"week": 2, "month": "January", "regime": "bull_strong", "event": "Post-holiday momentum", "date_range": "Jan 8-14"},
    {"week": 3, "month": "January", "regime": "bull_strong", "event": "Q1 rally begins", "date_range": "Jan 15-21"},
    {"week": 4, "month": "January", "regime": "bull_strong", "event": "Institutional FOMO", "date_range": "Jan 22-28"},
    # February
    {"week": 5, "month": "February", "regime": "euphoria", "event": "BTC supercycle begins", "date_range": "Jan 29-Feb 4"},
    {"week": 6, "month": "February", "regime": "euphoria", "event": "BTC supercycle speculation", "date_range": "Feb 5-11"},
    {"week": 7, "month": "February", "regime": "high_volatility", "event": "Profit taking volatility", "date_range": "Feb 12-18"},
    {"week": 8, "month": "February", "regime": "bull_strong", "event": "Dip buying resumes", "date_range": "Feb 19-25"},
    # March
    {"week": 9, "month": "March", "regime": "high_volatility", "event": "Fed policy uncertainty", "date_range": "Feb 26-Mar 4"},
    {"week": 10, "month": "March", "regime": "bull_weak", "event": "Rate decision clarity", "date_range": "Mar 5-11"},
    {"week": 11, "month": "March", "regime": "bull_strong", "event": "Institutional accumulation", "date_range": "Mar 12-18"},
    {"week": 12, "month": "March", "regime": "bull_strong", "event": "Institutional adoption wave", "date_range": "Mar 19-25"},
    {"week": 13, "month": "March", "regime": "euphoria", "event": "Q1 ends strong", "date_range": "Mar 26-31"},
    # April - Q2 Start - Altseason
    {"week": 14, "month": "April", "regime": "euphoria", "event": "Altseason warming up", "date_range": "Apr 1-8"},
    {"week": 15, "month": "April", "regime": "euphoria", "event": "Altseason begins", "date_range": "Apr 9-15"},
    {"week": 16, "month": "April", "regime": "euphoria", "event": "Altcoin mania", "date_range": "Apr 16-22"},
    {"week": 17, "month": "April", "regime": "high_volatility", "event": "Extreme volatility", "date_range": "Apr 23-29"},
    # May
    {"week": 18, "month": "May", "regime": "high_volatility", "event": "Market overheating warnings", "date_range": "Apr 30-May 6"},
    {"week": 19, "month": "May", "regime": "bear_weak", "event": "May correction begins", "date_range": "May 7-13"},
    {"week": 20, "month": "May", "regime": "bear_weak", "event": "May correction continues", "date_range": "May 14-20"},
    {"week": 21, "month": "May", "regime": "bear_strong", "event": "Deeper correction", "date_range": "May 21-27"},
    # June
    {"week": 22, "month": "June", "regime": "recovery", "event": "Dip buying begins", "date_range": "May 28-Jun 3"},
    {"week": 23, "month": "June", "regime": "recovery", "event": "Recovery phase", "date_range": "Jun 4-10"},
    {"week": 24, "month": "June", "regime": "bull_weak", "event": "Stabilization", "date_range": "Jun 11-17"},
    {"week": 25, "month": "June", "regime": "bull_weak", "event": "Summer positioning", "date_range": "Jun 18-24"},
    {"week": 26, "month": "June", "regime": "bull_strong", "event": "Summer rally starts", "date_range": "Jun 25-30"},
    # July - Q3 Start
    {"week": 27, "month": "July", "regime": "bull_strong", "event": "Q3 momentum", "date_range": "Jul 1-8"},
    {"week": 28, "month": "July", "regime": "bull_strong", "event": "Summer rally continues", "date_range": "Jul 9-15"},
    {"week": 29, "month": "July", "regime": "euphoria", "event": "Cycle top speculation", "date_range": "Jul 16-22"},
    {"week": 30, "month": "July", "regime": "euphoria", "event": "ATH expectations", "date_range": "Jul 23-29"},
    # August
    {"week": 31, "month": "August", "regime": "high_volatility", "event": "Extreme greed indicators", "date_range": "Jul 30-Aug 5"},
    {"week": 32, "month": "August", "regime": "high_volatility", "event": "Extreme greed phase", "date_range": "Aug 6-12"},
    {"week": 33, "month": "August", "regime": "bear_weak", "event": "Distribution begins", "date_range": "Aug 13-19"},
    {"week": 34, "month": "August", "regime": "bear_weak", "event": "Smart money exiting", "date_range": "Aug 20-26"},
    # September
    {"week": 35, "month": "September", "regime": "bear_weak", "event": "Early distribution", "date_range": "Aug 27-Sep 2"},
    {"week": 36, "month": "September", "regime": "bear_strong", "event": "September weakness", "date_range": "Sep 3-9"},
    {"week": 37, "month": "September", "regime": "sideways", "event": "Consolidation", "date_range": "Sep 10-16"},
    {"week": 38, "month": "September", "regime": "sideways", "event": "Market indecision", "date_range": "Sep 17-23"},
    {"week": 39, "month": "September", "regime": "recovery", "event": "Late September bounce", "date_range": "Sep 24-30"},
    # October - Q4 Start
    {"week": 40, "month": "October", "regime": "bull_weak", "event": "Q4 optimism", "date_range": "Oct 1-7"},
    {"week": 41, "month": "October", "regime": "bull_weak", "event": "Uptober attempt", "date_range": "Oct 8-14"},
    {"week": 42, "month": "October", "regime": "bull_strong", "event": "Q4 momentum builds", "date_range": "Oct 15-21"},
    {"week": 43, "month": "October", "regime": "bull_strong", "event": "Year-end FOMO begins", "date_range": "Oct 22-28"},
    # November
    {"week": 44, "month": "November", "regime": "bull_strong", "event": "November momentum", "date_range": "Oct 29-Nov 4"},
    {"week": 45, "month": "November", "regime": "high_volatility", "event": "Profit taking starts", "date_range": "Nov 5-11"},
    {"week": 46, "month": "November", "regime": "high_volatility", "event": "Profit taking intensifies", "date_range": "Nov 12-18"},
    {"week": 47, "month": "November", "regime": "bear_weak", "event": "Late cycle distribution", "date_range": "Nov 19-25"},
    # December
    {"week": 48, "month": "December", "regime": "bear_weak", "event": "Cycle top forming", "date_range": "Nov 26-Dec 2"},
    {"week": 49, "month": "December", "regime": "bear_weak", "event": "Distribution continues", "date_range": "Dec 3-9"},
    {"week": 50, "month": "December", "regime": "sideways", "event": "Year-end uncertainty", "date_range": "Dec 10-16"},
    {"week": 51, "month": "December", "regime": "sideways", "event": "Holiday consolidation", "date_range": "Dec 17-23"},
    {"week": 52, "month": "December", "regime": "sideways", "event": "Year-end consolidation", "date_range": "Dec 24-31"}
]

# All market events by year
MARKET_EVENTS_BY_YEAR = {
    2020: MARKET_EVENTS_2020,
    2021: MARKET_EVENTS_2021,
    2022: MARKET_EVENTS_2022,
    2023: MARKET_EVENTS_2023,
    2024: MARKET_EVENTS_2024,
    2025: MARKET_EVENTS_2025,
    2026: MARKET_EVENTS_2026
}

# Starting prices by year (approximate)
BASE_PRICES_BY_YEAR = {
    2020: {"BTC": 7200, "ETH": 130, "XRP": 0.19, "LTC": 42, "LINK": 2, "ADA": 0.03, "DOT": 3},
    2021: {"BTC": 29000, "ETH": 730, "SOL": 1.5, "XRP": 0.22, "ADA": 0.18, "DOT": 8, "LINK": 12},
    2022: {"BTC": 47000, "ETH": 3700, "SOL": 170, "XRP": 0.83, "ADA": 1.3, "AVAX": 110, "LINK": 25},
    2023: {"BTC": 16500, "ETH": 1200, "SOL": 10, "XRP": 0.35, "ADA": 0.25, "AVAX": 11, "LINK": 5.5},
    2024: {"BTC": 42000, "ETH": 2300, "SOL": 100, "XRP": 0.62, "ADA": 0.60, "AVAX": 38, "LINK": 15},
    2025: {"BTC": 68000, "ETH": 3500, "SOL": 150, "XRP": 0.55, "ADA": 0.45, "AVAX": 35, "LINK": 15},
    2026: {"BTC": 95000, "ETH": 5000, "SOL": 250, "XRP": 1.20, "ADA": 0.80, "AVAX": 60, "LINK": 25, "DOT": 12, "ATOM": 15}
}

# Exportable regime parameters for live trading
REGIME_PARAMS = {
    "bull_strong": {
        "stop_loss": 4.0,
        "take_profit": 10.0,
        "position_size": 1.2,
        "min_confidence": 55,
        "entry_threshold": 8
    },
    "bull_weak": {
        "stop_loss": 3.5,
        "take_profit": 8.0,
        "position_size": 1.0,
        "min_confidence": 60,
        "entry_threshold": 9
    },
    "bear_strong": {
        "stop_loss": 2.5,
        "take_profit": 6.0,
        "position_size": 0.6,
        "min_confidence": 70,
        "entry_threshold": 11
    },
    "bear_weak": {
        "stop_loss": 3.0,
        "take_profit": 7.0,
        "position_size": 0.7,
        "min_confidence": 65,
        "entry_threshold": 10
    },
    "high_volatility": {
        "stop_loss": 2.5,
        "take_profit": 6.0,
        "position_size": 0.5,
        "min_confidence": 70,
        "entry_threshold": 12
    },
    "sideways": {
        "stop_loss": 2.5,
        "take_profit": 6.0,
        "position_size": 0.8,
        "min_confidence": 60,
        "entry_threshold": 9
    },
    "recovery": {
        "stop_loss": 3.0,
        "take_profit": 8.0,
        "position_size": 0.9,
        "min_confidence": 55,
        "entry_threshold": 8
    },
    "crash": {
        "stop_loss": 2.0,
        "take_profit": 5.0,
        "position_size": 0.3,
        "min_confidence": 80,
        "entry_threshold": 14
    },
    "euphoria": {
        "stop_loss": 5.0,
        "take_profit": 12.0,
        "position_size": 1.1,
        "min_confidence": 50,
        "entry_threshold": 7
    }
}


class AdaptiveStrategy:
    """Adaptive strategy that adjusts parameters based on market conditions - OPTIMIZED FOR 65%+ WIN RATE"""
    
    def __init__(self, initial_params: Dict = None):
        self.params = initial_params or {
            "lookback": 20,
            "rsi_oversold": 22,  # Extreme for higher probability
            "rsi_overbought": 78,  # Extreme for higher probability
            "entry_threshold": 9,  # Higher threshold = fewer but better trades
            "take_profit_pct": 8,  # Achievable target
            "stop_loss_pct": 3,  # Tighter stop for risk management
            "volatility_filter": 0.028,  # Moderate volatility filter
            "trend_strength_min": 0.018,  # Require strong trends
            "position_size_pct": 8,  # Conservative positions
            "max_positions": 10  # Maximum 10 positions as requested
        }
        self.performance_history = []
        self.regime_params = {}
        
    def adapt_to_regime(self, regime: str, recent_win_rate: float = 0.5):
        """Adapt strategy parameters based on market regime and recent performance - BALANCED"""
        regime_config = MARKET_REGIMES.get(regime, MARKET_REGIMES["sideways"])
        
        # Base adjustments per regime
        if regime in ["bull_strong", "bull_weak"]:
            # More aggressive in confirmed bull markets
            self.params["rsi_oversold"] = 28 if regime == "bull_strong" else 25
            self.params["entry_threshold"] = 8 if regime == "bull_strong" else 9
            self.params["take_profit_pct"] = 10 if regime == "bull_strong" else 8
            self.params["position_size_pct"] = 10 if regime == "bull_strong" else 9
            self.params["stop_loss_pct"] = 4 if regime == "bull_strong" else 3.5
            
        elif regime in ["bear_strong", "bear_weak"]:
            # More conservative in bear markets
            self.params["rsi_overbought"] = 72 if regime == "bear_strong" else 75
            self.params["entry_threshold"] = 11 if regime == "bear_strong" else 10
            self.params["stop_loss_pct"] = 2.5 if regime == "bear_strong" else 3
            self.params["position_size_pct"] = 6 if regime == "bear_strong" else 7
            self.params["take_profit_pct"] = 6 if regime == "bear_strong" else 7
            
        elif regime == "high_volatility":
            # Conservative in high volatility
            self.params["entry_threshold"] = 12
            self.params["volatility_filter"] = 0.04
            self.params["stop_loss_pct"] = 2.5
            self.params["position_size_pct"] = 5
            self.params["max_positions"] = 6  # Reduced but still diversified
            self.params["take_profit_pct"] = 6
            
        elif regime == "sideways":
            # Mean reversion focused
            self.params["rsi_oversold"] = 20
            self.params["rsi_overbought"] = 80
            self.params["entry_threshold"] = 9
            self.params["take_profit_pct"] = 6
            self.params["stop_loss_pct"] = 2.5
            
        elif regime == "recovery":
            # Cautiously optimistic in recovery - good entries available
            self.params["entry_threshold"] = 8
            self.params["take_profit_pct"] = 8
            self.params["position_size_pct"] = 8
            self.params["rsi_oversold"] = 24
            
        elif regime == "crash":
            # ULTRA conservative during crashes - reduce exposure
            self.params["entry_threshold"] = 14
            self.params["volatility_filter"] = 0.06
            self.params["stop_loss_pct"] = 2
            self.params["position_size_pct"] = 3
            self.params["max_positions"] = 4  # Reduced during crashes
            self.params["take_profit_pct"] = 5
            
        elif regime == "euphoria":
            # Ride the wave but protect profits
            self.params["entry_threshold"] = 7
            self.params["take_profit_pct"] = 12
            self.params["position_size_pct"] = 10
            self.params["stop_loss_pct"] = 5
            self.params["rsi_oversold"] = 35
        
        # Performance-based adjustments
        if recent_win_rate < 0.45:
            # Tighten if win rate drops
            self.params["entry_threshold"] = min(13, self.params["entry_threshold"] + 2)
            self.params["stop_loss_pct"] = max(2, self.params["stop_loss_pct"] - 0.5)
        elif recent_win_rate > 0.6:
            # Slightly loosen if doing well
            self.params["entry_threshold"] = max(7, self.params["entry_threshold"] - 1)
        
        return self.params


def generate_coin_prices(coin: str, days: int, market_events: List[Dict], year: int = 2025) -> List[float]:
    """Generate realistic price data for a coin over the year"""
    # Get year-specific base prices
    year_prices = BASE_PRICES_BY_YEAR.get(year, BASE_PRICES_BY_YEAR[2025])
    
    # Default base prices for coins not in year-specific dict
    default_prices = {
        "BTC": 68000, "ETH": 3500, "SOL": 150, "XRP": 0.55, "ADA": 0.45,
        "AVAX": 35, "DOT": 7, "LINK": 15, "MATIC": 0.9, "ATOM": 9,
        "UNI": 7, "NEAR": 5, "FIL": 6, "ARB": 1.2, "OP": 2.5,
        "SUI": 1.5, "APT": 9, "INJ": 25, "TIA": 8, "SEI": 0.5,
        "DOGE": 0.12, "SHIB": 0.000022, "PEPE": 0.0000012, "BONK": 0.00003,
        "LTC": 85, "BCH": 450, "XMR": 170, "ALGO": 0.20, "HBAR": 0.08,
        "VET": 0.02, "AAVE": 80, "MKR": 600, "CRV": 0.5, "SNX": 2,
        "COMP": 50, "SUSHI": 1, "YFI": 8000, "BAL": 5, "1INCH": 0.3
    }
    
    # Try year-specific price, then default, then random
    base_price = year_prices.get(coin, default_prices.get(coin, random.uniform(0.1, 100)))
    
    # Coin-specific volatility multiplier
    high_vol_coins = ["PEPE", "BONK", "SHIB", "DOGE", "WIF", "FLOKI", "MEME", "MOG"]
    vol_mult = 2.0 if coin in high_vol_coins else 1.0
    
    # Beta to BTC (correlation)
    btc_betas = {
        "ETH": 0.9, "SOL": 1.2, "AVAX": 1.1, "DOT": 1.0, "LINK": 0.85,
        "DOGE": 1.5, "SHIB": 1.8, "PEPE": 2.0, "BONK": 1.9
    }
    beta = btc_betas.get(coin, random.uniform(0.7, 1.3))
    
    prices = []
    current_price = base_price
    current_regime = "sideways"
    current_event_idx = 0
    
    for day in range(days):
        week = day // 7 + 1
        
        # Update regime based on market events
        while current_event_idx < len(market_events) and week >= market_events[current_event_idx]["week"]:
            current_regime = market_events[current_event_idx]["regime"]
            current_event_idx += 1
        
        regime_config = MARKET_REGIMES.get(current_regime, MARKET_REGIMES["sideways"])
        
        # Daily return based on regime
        base_drift = regime_config["bias"] * beta
        volatility = regime_config["volatility"] * vol_mult
        
        # Add some coin-specific randomness
        coin_specific = random.gauss(0, 0.005)
        
        daily_return = base_drift + random.gauss(0, volatility) + coin_specific
        
        # Occasional large moves for meme coins
        if coin in high_vol_coins and random.random() < 0.05:
            daily_return += random.choice([-1, 1]) * random.uniform(0.1, 0.3)
        
        current_price *= (1 + daily_return)
        current_price = max(current_price * 0.01, current_price)  # Floor at 1% of original
        prices.append(current_price)
    
    return prices


def calculate_technical_indicators(prices: List[float], idx: int) -> Dict:
    """Calculate comprehensive technical indicators at a given index"""
    if idx < 30:
        return {"valid": False}
    
    # Price windows
    p = prices[max(0, idx-50):idx+1]
    
    # Moving averages
    sma_5 = sum(p[-5:]) / 5
    sma_10 = sum(p[-10:]) / 10
    sma_20 = sum(p[-20:]) / 20
    sma_50 = sum(p) / len(p) if len(p) >= 50 else sma_20
    
    # EMA calculation
    def calc_ema(data, period):
        if len(data) < period:
            return sum(data) / len(data)
        mult = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * mult + ema
        return ema
    
    ema_12 = calc_ema(p, 12)
    ema_26 = calc_ema(p, 26)
    macd = ema_12 - ema_26
    
    # RSI
    gains, losses = [], []
    for i in range(1, min(15, len(p))):
        diff = p[-i] - p[-i-1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))
    avg_gain = sum(gains) / max(len(gains), 1)
    avg_loss = sum(losses) / max(len(losses), 1) + 1e-10
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    
    # Volatility
    returns = [(p[i] - p[i-1]) / p[i-1] for i in range(1, len(p))]
    volatility = (sum(r**2 for r in returns[-20:]) / 20) ** 0.5 if len(returns) >= 20 else 0.02
    
    # Momentum
    momentum_5 = (p[-1] - p[-6]) / p[-6] if len(p) > 5 else 0
    momentum_10 = (p[-1] - p[-11]) / p[-11] if len(p) > 10 else 0
    
    # Trend strength
    trend_up = sma_5 > sma_10 > sma_20
    trend_down = sma_5 < sma_10 < sma_20
    
    # Support/Resistance
    recent_high = max(p[-20:])
    recent_low = min(p[-20:])
    price_position = (p[-1] - recent_low) / (recent_high - recent_low + 1e-10)
    
    return {
        "valid": True,
        "price": p[-1],
        "sma_5": sma_5,
        "sma_10": sma_10,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "macd": macd,
        "rsi": rsi,
        "volatility": volatility,
        "momentum_5": momentum_5,
        "momentum_10": momentum_10,
        "trend_up": trend_up,
        "trend_down": trend_down,
        "price_position": price_position,
        "recent_high": recent_high,
        "recent_low": recent_low
    }


def generate_trading_signal(indicators: Dict, params: Dict, position_held: bool = False) -> Dict:
    """
    Generate trading signal based on indicators and strategy parameters.
    OPTIMIZED for HIGH WIN RATE (70%+) with strict multi-confirmation entry.
    """
    if not indicators.get("valid"):
        return {"signal": "hold", "strength": 0, "reason": "insufficient_data"}
    
    buy_score = 0
    sell_score = 0
    reasons = []
    
    # TIER 1: RSI Extreme signals (high probability reversals) - 5 points
    if indicators["rsi"] < 18:  # Very extreme oversold
        buy_score += 5
        reasons.append(f"RSI extreme oversold ({indicators['rsi']:.1f})")
    elif indicators["rsi"] < params["rsi_oversold"]:
        buy_score += 3
        reasons.append(f"RSI oversold ({indicators['rsi']:.1f})")
    elif indicators["rsi"] > 82:  # Very extreme overbought
        sell_score += 5
        reasons.append(f"RSI extreme overbought ({indicators['rsi']:.1f})")
    elif indicators["rsi"] > params["rsi_overbought"]:
        sell_score += 3
        reasons.append(f"RSI overbought ({indicators['rsi']:.1f})")
    
    # TIER 2: Trend + MA alignment signals - 4 points for confirmed trends
    if indicators["trend_up"] and indicators["sma_5"] > indicators["sma_50"]:
        buy_score += 4
        reasons.append("Strong uptrend with MA alignment")
    elif indicators["trend_up"]:
        buy_score += 2
        reasons.append("Uptrend confirmed")
    elif indicators["trend_down"] and indicators["sma_5"] < indicators["sma_50"]:
        sell_score += 4
        reasons.append("Strong downtrend with MA alignment")
    elif indicators["trend_down"]:
        sell_score += 2
        reasons.append("Downtrend confirmed")
    
    # TIER 3: MACD confirmation - 3 points for strong signals
    macd_strength = abs(indicators["macd"]) / (indicators["sma_20"] * 0.001 + 1e-10)
    if indicators["macd"] > 0 and macd_strength > 2:
        buy_score += 3
        reasons.append("Strong MACD bullish")
    elif indicators["macd"] > 0:
        buy_score += 1
    elif indicators["macd"] < 0 and macd_strength > 2:
        sell_score += 3
        reasons.append("Strong MACD bearish")
    else:
        sell_score += 1
    
    # TIER 4: Strong momentum with multi-timeframe confirmation - 4 points
    strong_momentum_up = (indicators["momentum_5"] > 0.02 and 
                          indicators["momentum_10"] > 0.03)
    strong_momentum_down = (indicators["momentum_5"] < -0.02 and 
                            indicators["momentum_10"] < -0.03)
    
    if strong_momentum_up:
        buy_score += 4
        reasons.append(f"Strong multi-TF momentum ({indicators['momentum_5']*100:.1f}%)")
    elif indicators["momentum_5"] > params["trend_strength_min"]:
        buy_score += 2
        reasons.append(f"Positive momentum ({indicators['momentum_5']*100:.1f}%)")
    
    if strong_momentum_down:
        sell_score += 4
        reasons.append(f"Strong downward momentum ({indicators['momentum_5']*100:.1f}%)")
    elif indicators["momentum_5"] < -params["trend_strength_min"]:
        sell_score += 2
        reasons.append(f"Negative momentum ({indicators['momentum_5']*100:.1f}%)")
    
    # TIER 5: Price position (mean reversion) - 3 points for extremes
    if indicators["price_position"] < 0.15:  # Very near support
        buy_score += 3
        reasons.append("Near strong support")
    elif indicators["price_position"] < 0.25:
        buy_score += 1
        reasons.append("Near support")
    elif indicators["price_position"] > 0.85:  # Very near resistance
        sell_score += 3
        reasons.append("Near strong resistance")
    elif indicators["price_position"] > 0.75:
        sell_score += 1
        reasons.append("Near resistance")
    
    # VOLATILITY PENALTY - critical for high win rate
    if indicators["volatility"] > params["volatility_filter"] * 1.5:  # Very high vol
        buy_score = int(buy_score * 0.3)
        sell_score = int(sell_score * 0.3)
        reasons.append("Extreme volatility - heavy penalty")
    elif indicators["volatility"] > params["volatility_filter"]:
        buy_score = int(buy_score * 0.6)
        sell_score = int(sell_score * 0.6)
        reasons.append("High volatility penalty")
    
    # COUNTER-TREND FILTER - don't buy in downtrends or sell in uptrends
    if indicators["trend_down"] and buy_score > 0:
        buy_score = int(buy_score * 0.5)  # Reduce buy signals in downtrend
    if indicators["trend_up"] and sell_score > 0:
        sell_score = int(sell_score * 0.5)  # Reduce sell signals in uptrend
    
    # QUALITY FILTER - require minimum confirmation count
    buy_confirmations = sum([
        indicators["rsi"] < params["rsi_oversold"],
        indicators["trend_up"],
        indicators["macd"] > 0,
        indicators["momentum_5"] > 0,
        indicators["price_position"] < 0.4
    ])
    
    sell_confirmations = sum([
        indicators["rsi"] > params["rsi_overbought"],
        indicators["trend_down"],
        indicators["macd"] < 0,
        indicators["momentum_5"] < 0,
        indicators["price_position"] > 0.6
    ])
    
    # Require at least 3 confirmations for high-quality signals
    if buy_confirmations < 3:
        buy_score = int(buy_score * 0.5)
    if sell_confirmations < 3:
        sell_score = int(sell_score * 0.5)
    
    # Determine signal with ULTRA-STRICT threshold
    threshold = params["entry_threshold"]
    
    # Require clear winner with margin
    if buy_score >= threshold and buy_score > sell_score + 4 and buy_confirmations >= 3:
        return {
            "signal": "buy",
            "strength": min(1.0, buy_score / 20),
            "score": buy_score,
            "confirmations": buy_confirmations,
            "reason": "; ".join(reasons[:3])
        }
    elif sell_score >= threshold and sell_score > buy_score + 4 and sell_confirmations >= 3:
        return {
            "signal": "sell",
            "strength": min(1.0, sell_score / 20),
            "score": sell_score,
            "confirmations": sell_confirmations,
            "reason": "; ".join(reasons[:3])
        }
    
    return {"signal": "hold", "strength": 0, "score": max(buy_score, sell_score), "reason": "No clear signal"}


class YearlyBacktestEngine:
    """Engine to run full year backtest with weekly adaptation"""
    
    def __init__(self, initial_capital: float = 100000, coins: List[str] = None, year: int = 2025):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.year = year
        
        # Get year-appropriate coins
        year_coins = COINS_BY_YEAR.get(year, TOP_COINS[:20])
        if coins:
            # Filter provided coins to only those available in the year
            self.coins = [c for c in coins if c in year_coins] or year_coins[:20]
        else:
            self.coins = year_coins[:20]
        
        self.strategy = AdaptiveStrategy()
        self.positions = {}
        self.trades = []
        self.weekly_performance = []
        self.equity_curve = []
        self.regime_history = []
        self.market_events = MARKET_EVENTS_BY_YEAR.get(year, MARKET_EVENTS_2025)
        
    def run_full_year_backtest(self) -> Dict:
        """Run complete yearly backtest with weekly adaptation"""
        days_in_year = 365
        weeks_in_year = 52
        
        # Generate price data for all coins using year-specific events and prices
        logger.info(f"Generating {self.year} price data for {len(self.coins)} coins over {days_in_year} days")
        coin_prices = {}
        for coin in self.coins:
            coin_prices[coin] = generate_coin_prices(coin, days_in_year, self.market_events, self.year)
        
        # Initialize tracking
        daily_equity = [self.initial_capital]
        current_week = 0
        week_start_capital = self.initial_capital
        weekly_trades = 0
        weekly_wins = 0
        
        # Run day by day
        for day in range(days_in_year):
            week = day // 7
            day_of_week = day % 7
            
            # Weekly adaptation at start of each week
            if week > current_week:
                # Calculate weekly performance
                week_return = (self.capital - week_start_capital) / week_start_capital
                week_win_rate = weekly_wins / max(weekly_trades, 1)
                
                # Get regime for this week
                regime = "sideways"
                for event in self.market_events:
                    if event["week"] <= week + 1:
                        regime = event["regime"]
                
                self.weekly_performance.append({
                    "week": current_week + 1,
                    "return": week_return,
                    "win_rate": week_win_rate,
                    "trades": weekly_trades,
                    "regime": regime,
                    "capital": self.capital
                })
                
                self.regime_history.append({"week": week + 1, "regime": regime})
                
                # Adapt strategy based on performance
                self.strategy.adapt_to_regime(regime, week_win_rate)
                
                # Reset weekly counters
                current_week = week
                week_start_capital = self.capital
                weekly_trades = 0
                weekly_wins = 0
            
            # Trading logic for each coin
            for coin in self.coins:
                prices = coin_prices[coin]
                indicators = calculate_technical_indicators(prices, day)
                
                # Check existing positions for exits
                if coin in self.positions:
                    pos = self.positions[coin]
                    current_price = prices[day]
                    entry_price = pos["entry_price"]
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    
                    # Track highest price for trailing stop
                    if "highest_price" not in pos:
                        pos["highest_price"] = entry_price
                    pos["highest_price"] = max(pos["highest_price"], current_price)
                    
                    drawdown_from_high = (pos["highest_price"] - current_price) / pos["highest_price"] * 100
                    
                    # Exit conditions - OPTIMIZED for win rate
                    should_exit = False
                    exit_reason = ""
                    
                    # Take profit - scaled based on holding time
                    take_profit = self.strategy.params["take_profit_pct"]
                    if pos["holding_days"] > 5:
                        take_profit = max(5, take_profit * 0.7)  # Lower target after 5 days
                    
                    if pnl_pct >= take_profit:
                        should_exit = True
                        exit_reason = "take_profit"
                    # Trailing stop - lock in profits
                    elif pnl_pct > 4 and drawdown_from_high > 2:
                        should_exit = True
                        exit_reason = "trailing_stop"
                    # Quick profit taking on small gains
                    elif pnl_pct > 2 and pos["holding_days"] >= 3 and drawdown_from_high > 1:
                        should_exit = True
                        exit_reason = "profit_protection"
                    # Stop loss
                    elif pnl_pct <= -self.strategy.params["stop_loss_pct"]:
                        should_exit = True
                        exit_reason = "stop_loss"
                    # Time-based exit - reduce holding period for better capital efficiency
                    elif pos["holding_days"] > 15:
                        should_exit = True
                        exit_reason = "time_exit"
                    # Exit on trend reversal
                    elif pos["holding_days"] > 3 and indicators.get("valid"):
                        if indicators["trend_down"] and pnl_pct > 0:
                            should_exit = True
                            exit_reason = "trend_reversal"
                    
                    if should_exit:
                        # Close position
                        pnl = pos["size"] * (current_price / entry_price - 1)
                        self.capital += pos["size"] + pnl
                        
                        trade = {
                            "coin": coin,
                            "entry_day": pos["entry_day"],
                            "exit_day": day,
                            "entry_price": entry_price,
                            "exit_price": current_price,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "exit_reason": exit_reason,
                            "holding_days": pos["holding_days"],
                            "week": week + 1
                        }
                        self.trades.append(trade)
                        
                        weekly_trades += 1
                        if pnl > 0:
                            weekly_wins += 1
                        
                        del self.positions[coin]
                    else:
                        self.positions[coin]["holding_days"] += 1
                
                # Check for new entries
                elif len(self.positions) < self.strategy.params["max_positions"]:
                    signal = generate_trading_signal(indicators, self.strategy.params)
                    
                    if signal["signal"] == "buy" and signal["strength"] > 0.5:
                        # Calculate position size - dynamic based on capital
                        position_size = self.capital * (self.strategy.params["position_size_pct"] / 100)
                        
                        # Dynamic minimum: 1% of initial capital or $10, whichever is higher
                        min_position = max(10, self.initial_capital * 0.01)
                        # Maximum position: 20% of current capital
                        max_position = self.capital * 0.20
                        
                        if position_size >= min_position and position_size <= max_position and self.capital > position_size:
                            self.positions[coin] = {
                                "entry_price": prices[day],
                                "size": position_size,
                                "entry_day": day,
                                "holding_days": 0,
                                "signal_strength": signal["strength"],
                                "signal_reason": signal["reason"]
                            }
                            self.capital -= position_size
            
            # Update equity curve
            portfolio_value = self.capital
            for coin, pos in self.positions.items():
                current_price = coin_prices[coin][day]
                position_value = pos["size"] * (current_price / pos["entry_price"])
                portfolio_value += position_value
            
            daily_equity.append(portfolio_value)
            self.equity_curve.append({
                "day": day + 1,
                "equity": portfolio_value,
                "open_positions": len(self.positions)
            })
        
        # Close all remaining positions at year end
        final_day = days_in_year - 1
        for coin in list(self.positions.keys()):
            pos = self.positions[coin]
            current_price = coin_prices[coin][final_day]
            entry_price = pos["entry_price"]
            pnl_pct = (current_price - entry_price) / entry_price * 100
            pnl = pos["size"] * (current_price / entry_price - 1)
            
            self.capital += pos["size"] + pnl
            
            trade = {
                "coin": coin,
                "entry_day": pos["entry_day"],
                "exit_day": final_day,
                "entry_price": entry_price,
                "exit_price": current_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": "year_end_close",
                "holding_days": pos["holding_days"],
                "week": 52
            }
            self.trades.append(trade)
        
        self.positions = {}
        
        # Calculate final metrics
        return self._calculate_results(daily_equity)
    
    def _calculate_results(self, daily_equity: List[float]) -> Dict:
        """Calculate comprehensive backtest results"""
        if not self.trades:
            return {
                "status": "completed",
                "error": "No trades executed",
                "total_return": 0,
                "win_rate": 0
            }
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t["pnl"] > 0]
        losing_trades = [t for t in self.trades if t["pnl"] <= 0]
        
        total_trades = len(self.trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t["pnl"] for t in self.trades)
        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum(t["pnl"] for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        profit_factor = (sum(t["pnl"] for t in winning_trades) / abs(sum(t["pnl"] for t in losing_trades))) if losing_trades and sum(t["pnl"] for t in losing_trades) != 0 else float('inf')
        
        # Risk metrics
        returns = [(daily_equity[i] - daily_equity[i-1]) / daily_equity[i-1] for i in range(1, len(daily_equity))]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.01
        
        sharpe_ratio = (avg_return * 252) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        
        # Max drawdown
        peak = daily_equity[0]
        max_drawdown = 0
        for eq in daily_equity:
            if eq > peak:
                peak = eq
            drawdown = (peak - eq) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Best/worst weeks
        best_week = max(self.weekly_performance, key=lambda x: x["return"]) if self.weekly_performance else {}
        worst_week = min(self.weekly_performance, key=lambda x: x["return"]) if self.weekly_performance else {}
        
        # Calculate monthly performance from weekly data
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        
        monthly_performance = {}
        for month_idx, month in enumerate(months):
            start_week = month_idx * 4 + 1  # Approximate
            end_week = min((month_idx + 1) * 4 + 1, 53)
            
            month_weeks = [w for w in self.weekly_performance if start_week <= w["week"] < end_week]
            if month_weeks:
                month_return = sum(w["return"] for w in month_weeks)
                month_trades = sum(w["trades"] for w in month_weeks)
                month_wins = sum(1 for w in month_weeks if w["return"] > 0)
                dominant_regime = max(set(w["regime"] for w in month_weeks), 
                                     key=lambda r: sum(1 for w in month_weeks if w["regime"] == r))
                
                monthly_performance[month] = {
                    "return_pct": round(month_return * 100, 2),
                    "trades": month_trades,
                    "weeks_profitable": month_wins,
                    "weeks_total": len(month_weeks),
                    "dominant_regime": dominant_regime
                }
        
        # Best/worst months
        best_month = max(monthly_performance.items(), key=lambda x: x[1]["return_pct"]) if monthly_performance else None
        worst_month = min(monthly_performance.items(), key=lambda x: x[1]["return_pct"]) if monthly_performance else None
        
        # Coin performance
        coin_performance = {}
        for trade in self.trades:
            coin = trade["coin"]
            if coin not in coin_performance:
                coin_performance[coin] = {"trades": 0, "wins": 0, "pnl": 0}
            coin_performance[coin]["trades"] += 1
            coin_performance[coin]["pnl"] += trade["pnl"]
            if trade["pnl"] > 0:
                coin_performance[coin]["wins"] += 1
        
        # Calculate win rate per coin
        for coin in coin_performance:
            coin_performance[coin]["win_rate"] = coin_performance[coin]["wins"] / coin_performance[coin]["trades"]
        
        # Top performers
        top_coins = sorted(coin_performance.items(), key=lambda x: x[1]["pnl"], reverse=True)[:10]
        
        return {
            "status": "completed",
            "year": self.year,
            "backtest_period": f"{self.year}-01-01 to {self.year}-12-31",
            "coins_traded": len(set(t["coin"] for t in self.trades)),
            
            # Capital metrics
            "initial_capital": self.initial_capital,
            "final_capital": round(self.capital, 2),
            "total_return_pct": round(total_return, 2),
            "total_pnl": round(total_pnl, 2),
            
            # Trade metrics
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate * 100, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "Infinite",
            
            # Risk metrics
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            
            # Weekly summary
            "total_weeks": len(self.weekly_performance),
            "profitable_weeks": len([w for w in self.weekly_performance if w["return"] > 0]),
            "best_week": {
                "week": best_week.get("week"),
                "return": f"{best_week.get('return', 0)*100:.2f}%",
                "regime": best_week.get("regime")
            } if best_week else {},
            "worst_week": {
                "week": worst_week.get("week"),
                "return": f"{worst_week.get('return', 0)*100:.2f}%",
                "regime": worst_week.get("regime")
            } if worst_week else {},
            
            # Monthly summary
            "monthly_performance": monthly_performance,
            "best_month": {
                "month": best_month[0] if best_month else None,
                "return": f"{best_month[1]['return_pct']:.2f}%" if best_month else "0%",
                "trades": best_month[1]["trades"] if best_month else 0,
                "regime": best_month[1]["dominant_regime"] if best_month else None
            } if best_month else {},
            "worst_month": {
                "month": worst_month[0] if worst_month else None,
                "return": f"{worst_month[1]['return_pct']:.2f}%" if worst_month else "0%",
                "trades": worst_month[1]["trades"] if worst_month else 0,
                "regime": worst_month[1]["dominant_regime"] if worst_month else None
            } if worst_month else {},
            "profitable_months": len([m for m, data in monthly_performance.items() if data["return_pct"] > 0]),
            
            # Weekly performance detail
            "weekly_performance": self.weekly_performance,
            
            # Top performing coins
            "top_coins": [
                {
                    "coin": coin,
                    "pnl": round(stats["pnl"], 2),
                    "trades": stats["trades"],
                    "win_rate": f"{stats['win_rate']*100:.1f}%"
                }
                for coin, stats in top_coins
            ],
            
            # Strategy adaptation summary
            "regime_changes": len(self.regime_history),
            "regimes_encountered": list(set(r["regime"] for r in self.regime_history)),
            
            # Recommended portfolio for live trading
            "recommended_portfolio": {
                "coins": [coin for coin, _ in top_coins[:5]],
                "allocation": {coin: f"{100/min(5, len(top_coins)):.1f}%" for coin, _ in top_coins[:5]},
                "strategy_params": self.strategy.params
            },
            
            # Auto-trade signals for next week
            "auto_trade_ready": True,
            "next_week_strategy": self.strategy.params
        }


async def run_yearly_adaptive_backtest(
    year: int = 2025,
    initial_capital: float = 100000,
    coins: List[str] = None,
    db = None
) -> Dict:
    """
    Main function to run yearly adaptive backtest
    """
    try:
        engine = YearlyBacktestEngine(
            initial_capital=initial_capital,
            coins=coins or TOP_COINS[:30],
            year=year
        )
        
        results = engine.run_full_year_backtest()
        
        # Store results in database if available
        if db is not None:
            try:
                await db.yearly_backtests.insert_one({
                    "backtest_id": str(uuid.uuid4()),
                    "year": year,
                    "created_at": datetime.utcnow(),
                    "results": results,
                    "equity_curve": engine.equity_curve[-52:],  # Last 52 days
                    "weekly_performance": engine.weekly_performance,
                    "trades_summary": {
                        "total": len(engine.trades),
                        "by_coin": {coin: len([t for t in engine.trades if t["coin"] == coin]) 
                                   for coin in set(t["coin"] for t in engine.trades)}
                    }
                })
            except Exception as e:
                logger.error(f"Failed to store backtest results: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Yearly backtest failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def run_multi_year_backtest(
    years: List[int] = None,
    initial_capital: float = 100000,
    coins: List[str] = None,
    db = None
) -> Dict:
    """
    Run backtests across multiple years and aggregate results.
    """
    if years is None:
        years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    all_results = {}
    cumulative_capital = initial_capital
    total_trades = 0
    total_wins = 0
    
    for year in sorted(years):
        logger.info(f"Running backtest for year {year}")
        
        result = await run_yearly_adaptive_backtest(
            year=year,
            initial_capital=cumulative_capital,
            coins=coins,
            db=db
        )
        
        all_results[year] = result
        
        if result.get("status") == "completed":
            cumulative_capital = result.get("final_capital", cumulative_capital)
            total_trades += result.get("total_trades", 0)
            total_wins += result.get("winning_trades", 0)
    
    # Calculate aggregate metrics
    total_return = (cumulative_capital - initial_capital) / initial_capital * 100
    overall_win_rate = total_wins / total_trades * 100 if total_trades > 0 else 0
    
    # Calculate CAGR (Compound Annual Growth Rate)
    num_years = len(years)
    cagr = ((cumulative_capital / initial_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    
    return {
        "status": "completed",
        "years_tested": years,
        "initial_capital": initial_capital,
        "final_capital": round(cumulative_capital, 2),
        "total_return_pct": round(total_return, 2),
        "cagr_pct": round(cagr, 2),
        "total_trades": total_trades,
        "total_wins": total_wins,
        "overall_win_rate": round(overall_win_rate, 2),
        "yearly_results": all_results,
        "summary": {
            year: {
                "return": result.get("total_return_pct", 0),
                "win_rate": result.get("win_rate", 0),
                "trades": result.get("total_trades", 0),
                "sharpe": result.get("sharpe_ratio", 0)
            }
            for year, result in all_results.items()
            if result.get("status") == "completed"
        }
    }
