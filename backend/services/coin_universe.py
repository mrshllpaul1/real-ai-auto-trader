"""
Extended Coin Universe for AI Training
Contains 100+ coins that the AI can analyze and learn from.
"""

# Full coin universe with CoinCodex symbols
COIN_UNIVERSE = {
    # Major coins (Top 10)
    'bitcoin': {'symbol': 'BTC', 'category': 'major', 'launch': '2009-01-03'},
    'ethereum': {'symbol': 'ETH', 'category': 'major', 'launch': '2015-07-30'},
    'ripple': {'symbol': 'XRP', 'category': 'major', 'launch': '2012-01-01'},
    'litecoin': {'symbol': 'LTC', 'category': 'major', 'launch': '2011-10-07'},
    'cardano': {'symbol': 'ADA', 'category': 'major', 'launch': '2017-09-29'},
    'solana': {'symbol': 'SOL', 'category': 'major', 'launch': '2020-04-10'},
    'polkadot': {'symbol': 'DOT', 'category': 'major', 'launch': '2020-05-26'},
    'dogecoin': {'symbol': 'DOGE', 'category': 'major', 'launch': '2013-12-06'},
    'avalanche': {'symbol': 'AVAX', 'category': 'major', 'launch': '2020-09-21'},
    'chainlink': {'symbol': 'LINK', 'category': 'major', 'launch': '2017-09-19'},
    
    # Large caps
    'binancecoin': {'symbol': 'BNB', 'category': 'large', 'launch': '2017-07-25'},
    'tron': {'symbol': 'TRX', 'category': 'large', 'launch': '2017-08-28'},
    'polygon': {'symbol': 'MATIC', 'category': 'large', 'launch': '2019-04-22'},
    'shiba-inu': {'symbol': 'SHIB', 'category': 'large', 'launch': '2020-08-01'},
    'uniswap': {'symbol': 'UNI', 'category': 'large', 'launch': '2020-09-17'},
    'cosmos': {'symbol': 'ATOM', 'category': 'large', 'launch': '2019-03-14'},
    'stellar': {'symbol': 'XLM', 'category': 'large', 'launch': '2014-07-31'},
    'monero': {'symbol': 'XMR', 'category': 'large', 'launch': '2014-04-18'},
    'ethereum-classic': {'symbol': 'ETC', 'category': 'large', 'launch': '2016-07-20'},
    'bitcoin-cash': {'symbol': 'BCH', 'category': 'large', 'launch': '2017-08-01'},
    
    # Mid caps - Layer 1s
    'near': {'symbol': 'NEAR', 'category': 'mid', 'launch': '2020-04-22'},
    'aptos': {'symbol': 'APT', 'category': 'mid', 'launch': '2022-10-12'},
    'sui': {'symbol': 'SUI', 'category': 'mid', 'launch': '2023-05-03'},
    'algorand': {'symbol': 'ALGO', 'category': 'mid', 'launch': '2019-06-20'},
    'fantom': {'symbol': 'FTM', 'category': 'mid', 'launch': '2018-06-15'},
    'hedera': {'symbol': 'HBAR', 'category': 'mid', 'launch': '2019-09-16'},
    'internet-computer': {'symbol': 'ICP', 'category': 'mid', 'launch': '2021-05-10'},
    'vechain': {'symbol': 'VET', 'category': 'mid', 'launch': '2017-08-22'},
    'tezos': {'symbol': 'XTZ', 'category': 'mid', 'launch': '2018-06-30'},
    'eos': {'symbol': 'EOS', 'category': 'mid', 'launch': '2017-07-01'},
    
    # Mid caps - Layer 2s
    'arbitrum': {'symbol': 'ARB', 'category': 'mid', 'launch': '2021-08-31'},
    'optimism': {'symbol': 'OP', 'category': 'mid', 'launch': '2021-12-16'},
    'immutable-x': {'symbol': 'IMX', 'category': 'mid', 'launch': '2021-04-08'},
    'starknet': {'symbol': 'STRK', 'category': 'mid', 'launch': '2024-02-20'},
    
    # DeFi
    'aave': {'symbol': 'AAVE', 'category': 'defi', 'launch': '2020-10-02'},
    'maker': {'symbol': 'MKR', 'category': 'defi', 'launch': '2017-12-18'},
    'compound': {'symbol': 'COMP', 'category': 'defi', 'launch': '2020-06-15'},
    'curve-dao-token': {'symbol': 'CRV', 'category': 'defi', 'launch': '2020-08-13'},
    'lido-dao': {'symbol': 'LDO', 'category': 'defi', 'launch': '2021-01-05'},
    'pancakeswap': {'symbol': 'CAKE', 'category': 'defi', 'launch': '2020-09-28'},
    'sushiswap': {'symbol': 'SUSHI', 'category': 'defi', 'launch': '2020-08-28'},
    'yearn-finance': {'symbol': 'YFI', 'category': 'defi', 'launch': '2020-07-17'},
    '1inch': {'symbol': '1INCH', 'category': 'defi', 'launch': '2020-12-25'},
    'synthetix': {'symbol': 'SNX', 'category': 'defi', 'launch': '2018-03-01'},
    'balancer': {'symbol': 'BAL', 'category': 'defi', 'launch': '2020-06-23'},
    'frax': {'symbol': 'FRAX', 'category': 'defi', 'launch': '2020-12-21'},
    'gmx': {'symbol': 'GMX', 'category': 'defi', 'launch': '2021-09-01'},
    'dydx': {'symbol': 'DYDX', 'category': 'defi', 'launch': '2021-09-08'},
    'rocket-pool': {'symbol': 'RPL', 'category': 'defi', 'launch': '2017-11-01'},
    
    # Gaming/Metaverse
    'the-sandbox': {'symbol': 'SAND', 'category': 'gaming', 'launch': '2020-08-14'},
    'decentraland': {'symbol': 'MANA', 'category': 'gaming', 'launch': '2017-08-18'},
    'axie-infinity': {'symbol': 'AXS', 'category': 'gaming', 'launch': '2020-11-04'},
    'enjincoin': {'symbol': 'ENJ', 'category': 'gaming', 'launch': '2017-11-01'},
    'gala': {'symbol': 'GALA', 'category': 'gaming', 'launch': '2020-09-16'},
    'illuvium': {'symbol': 'ILV', 'category': 'gaming', 'launch': '2021-03-30'},
    'apecoin': {'symbol': 'APE', 'category': 'gaming', 'launch': '2022-03-17'},
    'render-token': {'symbol': 'RNDR', 'category': 'gaming', 'launch': '2017-10-06'},
    
    # Infrastructure/Oracle
    'the-graph': {'symbol': 'GRT', 'category': 'infra', 'launch': '2020-12-17'},
    'filecoin': {'symbol': 'FIL', 'category': 'infra', 'launch': '2020-10-15'},
    'arweave': {'symbol': 'AR', 'category': 'infra', 'launch': '2018-06-08'},
    'helium': {'symbol': 'HNT', 'category': 'infra', 'launch': '2019-07-29'},
    'ocean-protocol': {'symbol': 'OCEAN', 'category': 'infra', 'launch': '2019-05-06'},
    'band-protocol': {'symbol': 'BAND', 'category': 'infra', 'launch': '2019-09-18'},
    'api3': {'symbol': 'API3', 'category': 'infra', 'launch': '2020-12-01'},
    
    # Privacy
    'zcash': {'symbol': 'ZEC', 'category': 'privacy', 'launch': '2016-10-28'},
    'dash': {'symbol': 'DASH', 'category': 'privacy', 'launch': '2014-01-18'},
    'horizen': {'symbol': 'ZEN', 'category': 'privacy', 'launch': '2017-05-30'},
    'secret': {'symbol': 'SCRT', 'category': 'privacy', 'launch': '2020-02-13'},
    
    # Exchange tokens
    'cronos': {'symbol': 'CRO', 'category': 'exchange', 'launch': '2018-12-14'},
    'okb': {'symbol': 'OKB', 'category': 'exchange', 'launch': '2019-04-01'},
    'kucoin-token': {'symbol': 'KCS', 'category': 'exchange', 'launch': '2017-10-24'},
    'ftx-token': {'symbol': 'FTT', 'category': 'exchange', 'launch': '2019-05-08'},
    
    # Meme coins / High volatility
    'pepe': {'symbol': 'PEPE', 'category': 'meme', 'launch': '2023-04-14'},
    'floki': {'symbol': 'FLOKI', 'category': 'meme', 'launch': '2021-06-28'},
    'bonk': {'symbol': 'BONK', 'category': 'meme', 'launch': '2022-12-25'},
    'wojak': {'symbol': 'WOJAK', 'category': 'meme', 'launch': '2023-04-17'},
    'babydoge': {'symbol': 'BABYDOGE', 'category': 'meme', 'launch': '2021-06-01'},
    
    # AI/ML tokens
    'fetch-ai': {'symbol': 'FET', 'category': 'ai', 'launch': '2019-02-25'},
    'singularitynet': {'symbol': 'AGIX', 'category': 'ai', 'launch': '2017-12-21'},
    'ocean-protocol': {'symbol': 'OCEAN', 'category': 'ai', 'launch': '2019-05-06'},
    'numeraire': {'symbol': 'NMR', 'category': 'ai', 'launch': '2017-06-21'},
    'cortex': {'symbol': 'CTXC', 'category': 'ai', 'launch': '2018-04-01'},
    'bittensor': {'symbol': 'TAO', 'category': 'ai', 'launch': '2023-03-01'},
    'worldcoin': {'symbol': 'WLD', 'category': 'ai', 'launch': '2023-07-24'},
    
    # Cross-chain/Bridges
    'thorchain': {'symbol': 'RUNE', 'category': 'bridge', 'launch': '2019-07-23'},
    'wormhole': {'symbol': 'W', 'category': 'bridge', 'launch': '2024-04-03'},
    'multichain': {'symbol': 'MULTI', 'category': 'bridge', 'launch': '2021-01-20'},
    'synapse': {'symbol': 'SYN', 'category': 'bridge', 'launch': '2021-08-29'},
    
    # Storage
    'storj': {'symbol': 'STORJ', 'category': 'storage', 'launch': '2017-07-03'},
    'siacoin': {'symbol': 'SC', 'category': 'storage', 'launch': '2015-06-01'},
    
    # Older altcoins
    'nem': {'symbol': 'XEM', 'category': 'old', 'launch': '2015-03-31'},
    'iota': {'symbol': 'MIOTA', 'category': 'old', 'launch': '2017-06-13'},
    'neo': {'symbol': 'NEO', 'category': 'old', 'launch': '2016-08-01'},
    'waves': {'symbol': 'WAVES', 'category': 'old', 'launch': '2016-06-12'},
    'qtum': {'symbol': 'QTUM', 'category': 'old', 'launch': '2017-09-13'},
    'zilliqa': {'symbol': 'ZIL', 'category': 'old', 'launch': '2018-01-25'},
    'icon': {'symbol': 'ICX', 'category': 'old', 'launch': '2017-10-27'},
    'ontology': {'symbol': 'ONT', 'category': 'old', 'launch': '2018-03-08'},
    'ravencoin': {'symbol': 'RVN', 'category': 'old', 'launch': '2018-01-03'},
    'decred': {'symbol': 'DCR', 'category': 'old', 'launch': '2016-02-08'},
    
    # Newer promising
    'injective': {'symbol': 'INJ', 'category': 'new', 'launch': '2020-10-21'},
    'sei': {'symbol': 'SEI', 'category': 'new', 'launch': '2023-08-15'},
    'celestia': {'symbol': 'TIA', 'category': 'new', 'launch': '2023-10-31'},
    'blur': {'symbol': 'BLUR', 'category': 'new', 'launch': '2023-02-14'},
    'jito': {'symbol': 'JTO', 'category': 'new', 'launch': '2023-12-07'},
    'jupiter': {'symbol': 'JUP', 'category': 'new', 'launch': '2024-01-31'},
    'pyth': {'symbol': 'PYTH', 'category': 'new', 'launch': '2023-11-20'},
    'mantle': {'symbol': 'MNT', 'category': 'new', 'launch': '2023-07-17'},
}

# Categories for diversification
CATEGORIES = {
    'major': 'Blue chip, safest',
    'large': 'Large cap, relatively safe',
    'mid': 'Mid cap, moderate risk',
    'defi': 'DeFi protocols',
    'gaming': 'Gaming/Metaverse',
    'infra': 'Infrastructure',
    'privacy': 'Privacy coins',
    'exchange': 'Exchange tokens',
    'meme': 'Meme coins, high risk/reward',
    'ai': 'AI/ML tokens',
    'bridge': 'Cross-chain bridges',
    'storage': 'Storage protocols',
    'old': 'Older altcoins',
    'new': 'Newer promising projects'
}

def get_available_coins(date_str: str) -> list:
    """Get coins that existed at a given date"""
    from datetime import datetime
    target_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
    
    available = []
    for coin_id, info in COIN_UNIVERSE.items():
        launch = datetime.strptime(info['launch'], '%Y-%m-%d')
        if launch <= target_date:
            available.append(coin_id)
    
    return available

def get_coins_by_category(category: str) -> list:
    """Get all coins in a category"""
    return [coin_id for coin_id, info in COIN_UNIVERSE.items() 
            if info['category'] == category]

def get_gem_candidates() -> list:
    """Get coins that could be 'gems' (high risk/reward)"""
    gem_categories = ['meme', 'ai', 'new', 'gaming']
    return [coin_id for coin_id, info in COIN_UNIVERSE.items() 
            if info['category'] in gem_categories]

def get_all_coins() -> list:
    """Get all coins in the universe for training"""
    return list(COIN_UNIVERSE.keys())

def get_training_coins() -> list:
    """
    Get all coins for AI training - includes entire universe.
    Returns coins sorted by priority (major first, then by category).
    """
    priority_order = ['major', 'large', 'mid', 'defi', 'ai', 'gaming', 'infra', 'new', 'meme', 'bridge', 'storage', 'exchange', 'privacy', 'older']
    
    coins = []
    for category in priority_order:
        coins.extend(get_coins_by_category(category))
    
    # Add any remaining coins not in categories
    for coin_id in COIN_UNIVERSE.keys():
        if coin_id not in coins:
            coins.append(coin_id)
    
    return coins
