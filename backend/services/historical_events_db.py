"""
Historical Events Database
Downloads and stores major crypto events for AI training.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


# Major historical events to download
MAJOR_EVENTS = [
    # 2013-2014 Early Days
    {"date": "2013-04-10", "event": "Bitcoin crashes 83% from $266 to $45", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2013-10-02", "event": "Silk Road seized by FBI", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2013-11-29", "event": "Bitcoin hits $1,000 for first time", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2013-12-05", "event": "China bans banks from Bitcoin", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2014-02-24", "event": "Mt. Gox exchange collapse - 850k BTC lost", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2014-07-18", "event": "Dell accepts Bitcoin payments", "coins": ["BTC"], "impact": "positive", "category": "partnership"},
    
    # 2015-2016 Recovery
    {"date": "2015-01-04", "event": "Bitstamp hack - 19,000 BTC stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2015-06-03", "event": "New York introduces BitLicense", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2016-01-14", "event": "Mike Hearn declares Bitcoin failed", "coins": ["BTC"], "impact": "negative", "category": "technology"},
    {"date": "2016-06-17", "event": "The DAO hack - $60M stolen from Ethereum", "coins": ["ETH"], "impact": "negative", "category": "hack"},
    {"date": "2016-07-09", "event": "Bitcoin halving 2016", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2016-07-20", "event": "Ethereum hard fork creates ETC", "coins": ["ETH", "ETC"], "impact": "mixed", "category": "technology"},
    {"date": "2016-08-02", "event": "Bitfinex hack - 120,000 BTC stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    
    # 2017 Bull Run
    {"date": "2017-03-10", "event": "SEC rejects Winklevoss Bitcoin ETF", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2017-04-01", "event": "Japan recognizes Bitcoin as legal payment", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2017-08-01", "event": "Bitcoin Cash hard fork", "coins": ["BTC", "BCH"], "impact": "mixed", "category": "technology"},
    {"date": "2017-09-04", "event": "China bans ICOs", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2017-10-13", "event": "Bitcoin breaks $5,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2017-11-08", "event": "SegWit2x fork cancelled", "coins": ["BTC"], "impact": "mixed", "category": "technology"},
    {"date": "2017-12-07", "event": "NiceHash hack - $64M stolen", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2017-12-11", "event": "CBOE launches Bitcoin futures", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2017-12-17", "event": "Bitcoin reaches $20k ATH", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2017-12-22", "event": "Bitcoin crashes 45% in 5 days", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2018 Bear Market
    {"date": "2018-01-13", "event": "Ripple XRP reaches ATH $3.84", "coins": ["XRP"], "impact": "positive", "category": "milestone"},
    {"date": "2018-01-26", "event": "Coincheck hack - $530M NEM stolen", "coins": ["XEM"], "impact": "negative", "category": "hack"},
    {"date": "2018-02-06", "event": "Bitcoin drops below $6,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2018-03-07", "event": "SEC says crypto exchanges must register", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2018-06-11", "event": "South Korea exchange Coinrail hacked", "coins": ["BTC"], "impact": "negative", "category": "hack"},
    {"date": "2018-09-20", "event": "Goldman Sachs shelves crypto desk plans", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2018-11-14", "event": "Bitcoin crashes below $6,000 support", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2018-11-15", "event": "Bitcoin Cash hash war begins", "coins": ["BCH", "BSV"], "impact": "negative", "category": "technology"},
    {"date": "2018-12-15", "event": "Bitcoin hits $3,200 bear market bottom", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2019 Recovery
    {"date": "2019-02-07", "event": "QuadrigaCX founder dies with $190M", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2019-04-02", "event": "Bitcoin breaks $5,000 after 4 months", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2019-05-07", "event": "Binance hack - 7,000 BTC stolen", "coins": ["BTC", "BNB"], "impact": "negative", "category": "hack"},
    {"date": "2019-06-18", "event": "Facebook announces Libra cryptocurrency", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2019-06-26", "event": "Bitcoin reaches $13,800 yearly high", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2019-10-24", "event": "Xi Jinping endorses blockchain", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    
    # 2020-2021 Bull Run
    {"date": "2020-03-12", "event": "Black Thursday - BTC drops 50% in one day", "coins": ["BTC", "ETH"], "impact": "negative", "category": "macro"},
    {"date": "2020-05-11", "event": "Bitcoin halving 2020", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2020-07-27", "event": "US banks can custody crypto - OCC", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2020-08-11", "event": "MicroStrategy buys $250M Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2020-10-08", "event": "Square buys $50M Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2020-10-21", "event": "PayPal enables crypto buying", "coins": ["BTC", "ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2020-11-30", "event": "Bitcoin breaks 2017 ATH of $20k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2020-12-16", "event": "Bitcoin reaches $21,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2021 - Elon Era & NFT Boom
    {"date": "2021-01-02", "event": "Bitcoin reaches $30,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-01-08", "event": "Bitcoin hits $40,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-01-29", "event": "Elon Musk adds #Bitcoin to Twitter bio", "coins": ["BTC"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-02-04", "event": "Elon tweets about Dogecoin being people's crypto", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-02-08", "event": "Tesla buys $1.5B Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2021-02-19", "event": "Bitcoin market cap reaches $1 trillion", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-03-11", "event": "Beeple NFT sells for $69M", "coins": ["ETH"], "impact": "positive", "category": "milestone"},
    {"date": "2021-03-14", "event": "Bitcoin reaches $60,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-04-14", "event": "Coinbase IPO - COIN starts trading", "coins": ["BTC", "ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2021-04-16", "event": "Dogecoin surges 400% in a week", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-04-20", "event": "Dogecoin Day - Elon pumps DOGE", "coins": ["DOGE"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-05-08", "event": "Elon hosts SNL - DOGE crashes 30%", "coins": ["DOGE"], "impact": "negative", "category": "celebrity"},
    {"date": "2021-05-12", "event": "Tesla suspends BTC payments", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2021-05-13", "event": "Elon says looking for greener crypto", "coins": ["BTC", "DOGE"], "impact": "negative", "category": "celebrity"},
    {"date": "2021-05-19", "event": "China bans financial institutions from crypto", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-06-09", "event": "El Salvador makes Bitcoin legal tender", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2021-06-21", "event": "China shuts down Bitcoin miners", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-07-21", "event": "Elon and Jack Dorsey Bitcoin B-Word event", "coins": ["BTC"], "impact": "positive", "category": "celebrity"},
    {"date": "2021-09-07", "event": "El Salvador officially adopts Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2021-09-24", "event": "China declares all crypto transactions illegal", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2021-10-19", "event": "First Bitcoin futures ETF (BITO) launches", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2021-11-10", "event": "Bitcoin reaches ATH $69,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2021-11-10", "event": "Ethereum reaches ATH $4,870", "coins": ["ETH"], "impact": "positive", "category": "milestone"},
    {"date": "2021-12-04", "event": "Bitcoin flash crashes 22% to $42k", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2022 - Crash Year
    {"date": "2022-01-21", "event": "Russia proposes crypto ban", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2022-01-24", "event": "Bitcoin drops below $33,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-02-24", "event": "Russia invades Ukraine - crypto volatility", "coins": ["BTC"], "impact": "mixed", "category": "macro"},
    {"date": "2022-03-09", "event": "Biden signs crypto executive order", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2022-04-27", "event": "Central African Republic adopts Bitcoin", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2022-05-09", "event": "UST depeg begins - Terra collapse starts", "coins": ["LUNA", "UST"], "impact": "negative", "category": "hack"},
    {"date": "2022-05-12", "event": "Luna crashes 99% - $40B wiped out", "coins": ["LUNA"], "impact": "negative", "category": "hack"},
    {"date": "2022-06-13", "event": "Celsius freezes withdrawals", "coins": ["BTC", "ETH"], "impact": "negative", "category": "exchange"},
    {"date": "2022-06-18", "event": "Bitcoin drops below $18,000", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-07-01", "event": "Three Arrows Capital files bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2022-07-13", "event": "Celsius files for bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2022-09-15", "event": "Ethereum Merge - PoS transition", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2022-11-02", "event": "CoinDesk exposes FTX/Alameda balance sheet", "coins": ["FTT", "SOL"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-06", "event": "CZ announces Binance selling FTT", "coins": ["FTT", "BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-08", "event": "FTX halts withdrawals", "coins": ["FTT", "SOL"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-08", "event": "Binance backs out of FTX acquisition", "coins": ["BTC", "FTT"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-11", "event": "FTX files for bankruptcy - SBF resigns", "coins": ["BTC", "SOL", "FTT"], "impact": "negative", "category": "exchange"},
    {"date": "2022-11-12", "event": "FTX hacked - $600M drained", "coins": ["FTT"], "impact": "negative", "category": "hack"},
    {"date": "2022-11-21", "event": "Bitcoin hits $15,500 - 2-year low", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2022-12-12", "event": "SBF arrested in Bahamas", "coins": ["FTT"], "impact": "mixed", "category": "regulatory"},
    
    # 2023 Recovery
    {"date": "2023-01-14", "event": "Bitcoin breaks $20k - post-FTX recovery", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-01-21", "event": "Genesis files for bankruptcy", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2023-02-09", "event": "SEC charges Kraken for staking", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-03-08", "event": "Silvergate Bank announces liquidation", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2023-03-10", "event": "Silicon Valley Bank collapses", "coins": ["BTC", "USDC"], "impact": "mixed", "category": "macro"},
    {"date": "2023-03-12", "event": "Signature Bank closed by regulators", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2023-03-13", "event": "Bitcoin pumps 20% on banking fears", "coins": ["BTC"], "impact": "positive", "category": "macro"},
    {"date": "2023-04-14", "event": "Bitcoin breaks $30,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-04-17", "event": "Ethereum Shanghai upgrade - staking withdrawals", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2023-06-05", "event": "SEC sues Binance and CZ", "coins": ["BNB", "BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-06", "event": "SEC sues Coinbase", "coins": ["BTC", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-06-15", "event": "BlackRock files for spot Bitcoin ETF", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2023-07-13", "event": "Ripple wins partial victory vs SEC", "coins": ["XRP"], "impact": "positive", "category": "regulatory"},
    {"date": "2023-08-29", "event": "Grayscale wins lawsuit against SEC", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2023-10-16", "event": "Fake BlackRock ETF approval pumps BTC", "coins": ["BTC"], "impact": "mixed", "category": "institutional"},
    {"date": "2023-11-21", "event": "Binance settles with DOJ - $4.3B fine", "coins": ["BNB"], "impact": "negative", "category": "regulatory"},
    {"date": "2023-11-21", "event": "CZ steps down as Binance CEO", "coins": ["BNB"], "impact": "negative", "category": "exchange"},
    {"date": "2023-12-04", "event": "Bitcoin breaks $40,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2024 ETF Era
    {"date": "2024-01-02", "event": "Matrixport predicts SEC ETF rejection - BTC dumps", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2024-01-09", "event": "SEC Twitter hacked - fake ETF approval", "coins": ["BTC"], "impact": "mixed", "category": "regulatory"},
    {"date": "2024-01-10", "event": "SEC approves 11 spot Bitcoin ETFs", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-01-11", "event": "Bitcoin ETFs begin trading - $4.5B volume day 1", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-02-15", "event": "Bitcoin breaks $50,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-02-28", "event": "Bitcoin ETFs hit $6B daily volume", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-03-05", "event": "Bitcoin breaks previous ATH $69k", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-03-14", "event": "Bitcoin reaches new ATH $73,750", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-04-20", "event": "Bitcoin halving 2024", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2024-05-20", "event": "SEC approves Ethereum ETFs", "coins": ["ETH"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-06-27", "event": "Mt. Gox begins BTC repayments after 10 years", "coins": ["BTC"], "impact": "negative", "category": "exchange"},
    {"date": "2024-07-05", "event": "Germany sells 50,000 BTC seized from Movie2k", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2024-07-23", "event": "Ethereum ETFs begin trading", "coins": ["ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2024-08-05", "event": "Crypto market flash crash - Yen carry trade unwind", "coins": ["BTC", "ETH"], "impact": "negative", "category": "macro"},
    {"date": "2024-09-18", "event": "Fed cuts rates 50bps - first cut since 2020", "coins": ["BTC"], "impact": "positive", "category": "macro"},
    {"date": "2024-10-29", "event": "Microsoft shareholders to vote on Bitcoin treasury", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-11-05", "event": "Trump wins US election - crypto rallies", "coins": ["BTC", "DOGE"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-11-10", "event": "Bitcoin breaks $80,000 post-election", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-11-13", "event": "Bitcoin reaches $90,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-11-21", "event": "Gensler announces SEC resignation", "coins": ["BTC", "ETH", "XRP"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-11-22", "event": "Bitcoin touches $99,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-12-04", "event": "Bitcoin breaks $100,000 for first time", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-12-05", "event": "Trump nominates Paul Atkins as SEC Chair", "coins": ["BTC", "XRP"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-12-10", "event": "Microsoft shareholders reject Bitcoin treasury proposal", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2024-12-17", "event": "Bitcoin reaches ATH $108,000", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-12-18", "event": "Fed hawkish pivot - only 2 cuts in 2025", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2024-12-20", "event": "Bitcoin corrects to $92,000 on Fed fears", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # 2025 - Institutional Adoption Era
    {"date": "2025-01-02", "event": "Bitcoin starts 2025 at $94,500", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2025-01-06", "event": "MicroStrategy buys another 1,070 BTC", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2025-01-09", "event": "Bitcoin ETFs see $900M single day inflow", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2025-01-13", "event": "DOJ authorized to sell $6.5B Silk Road Bitcoin", "coins": ["BTC"], "impact": "negative", "category": "regulatory"},
    {"date": "2025-01-15", "event": "Trump team considers crypto-friendly Treasury picks", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-20", "event": "Trump inaugurated - pro-crypto administration begins", "coins": ["BTC", "SOL", "XRP"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-21", "event": "Trump signs executive order on digital assets", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-22", "event": "Bitcoin rallies to $105,000 on Trump orders", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2025-01-23", "event": "Strategic Bitcoin Reserve executive order signed", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-24", "event": "SEC drops several crypto enforcement cases", "coins": ["XRP", "SOL"], "impact": "positive", "category": "regulatory"},
    {"date": "2025-01-25", "event": "Solana reaches $250 - new ATH", "coins": ["SOL"], "impact": "positive", "category": "milestone"},
    {"date": "2025-01-27", "event": "Bitcoin corrects 10% on profit taking", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2025-01-28", "event": "DeepSeek AI causes tech/crypto correlation sell-off", "coins": ["BTC", "ETH"], "impact": "negative", "category": "macro"},
    {"date": "2025-01-29", "event": "FOMC holds rates steady as expected", "coins": ["BTC"], "impact": "mixed", "category": "macro"},
    {"date": "2025-01-30", "event": "Bitcoin ETFs reach $125B total AUM", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2025-01-31", "event": "XRP surges 30% on SEC case dismissal hopes", "coins": ["XRP"], "impact": "positive", "category": "regulatory"},
    
    # 2025 February onwards (projected/reported)
    {"date": "2025-02-01", "event": "Trump tariffs on China cause market volatility", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2025-02-03", "event": "Bitcoin drops to $91,000 on tariff fears", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    
    # Additional Historical Events - DeFi & Altcoins
    {"date": "2020-06-15", "event": "Compound launches COMP token - DeFi Summer begins", "coins": ["COMP", "ETH"], "impact": "positive", "category": "defi"},
    {"date": "2020-08-13", "event": "Yam Finance launches and crashes 90%", "coins": ["YAM", "ETH"], "impact": "negative", "category": "defi"},
    {"date": "2020-09-16", "event": "Uniswap airdrops UNI token - $1200 per user", "coins": ["UNI", "ETH"], "impact": "positive", "category": "defi"},
    {"date": "2020-09-28", "event": "SushiSwap vampire attack on Uniswap", "coins": ["SUSHI", "UNI"], "impact": "mixed", "category": "defi"},
    {"date": "2021-02-03", "event": "Dogecoin surges 800% in week on Reddit pump", "coins": ["DOGE"], "impact": "positive", "category": "meme"},
    {"date": "2021-03-22", "event": "Twitter founder Jack Dorsey sells first tweet as NFT", "coins": ["ETH"], "impact": "positive", "category": "nft"},
    {"date": "2021-05-05", "event": "Shiba Inu token surges 2000% in a week", "coins": ["SHIB"], "impact": "positive", "category": "meme"},
    {"date": "2021-08-18", "event": "Poly Network hack - $600M stolen and returned", "coins": ["ETH"], "impact": "negative", "category": "hack"},
    {"date": "2021-09-14", "event": "Arbitrum One mainnet launch", "coins": ["ETH", "ARB"], "impact": "positive", "category": "technology"},
    {"date": "2021-10-28", "event": "Facebook rebrands to Meta - metaverse coins pump", "coins": ["MANA", "SAND"], "impact": "positive", "category": "institutional"},
    {"date": "2021-11-01", "event": "Solana reaches $260 ATH", "coins": ["SOL"], "impact": "positive", "category": "milestone"},
    {"date": "2021-11-09", "event": "Avalanche launches $180M DeFi incentive program", "coins": ["AVAX"], "impact": "positive", "category": "defi"},
    {"date": "2021-12-09", "event": "Badger DAO hack - $120M stolen", "coins": ["BADGER", "ETH"], "impact": "negative", "category": "hack"},
    
    # 2022 Additional Events
    {"date": "2022-01-17", "event": "Wonderland TIME Treasury scandal breaks", "coins": ["TIME", "AVAX"], "impact": "negative", "category": "defi"},
    {"date": "2022-02-03", "event": "Wormhole bridge hack - $320M stolen", "coins": ["SOL", "ETH"], "impact": "negative", "category": "hack"},
    {"date": "2022-03-23", "event": "ApeCoin launches with $4B valuation", "coins": ["APE"], "impact": "positive", "category": "nft"},
    {"date": "2022-03-28", "event": "Ronin bridge hack - $625M stolen by North Korea", "coins": ["AXS", "ETH"], "impact": "negative", "category": "hack"},
    {"date": "2022-04-30", "event": "Otherside NFT mint crashes Ethereum gas to $5000", "coins": ["APE", "ETH"], "impact": "mixed", "category": "nft"},
    {"date": "2022-06-27", "event": "Harmony Horizon bridge hack - $100M stolen", "coins": ["ONE"], "impact": "negative", "category": "hack"},
    {"date": "2022-08-08", "event": "Tornado Cash sanctioned by US Treasury", "coins": ["TORN", "ETH"], "impact": "negative", "category": "regulatory"},
    {"date": "2022-09-06", "event": "Cardano Vasil hard fork launches", "coins": ["ADA"], "impact": "positive", "category": "technology"},
    {"date": "2022-10-06", "event": "BNB Chain halted after $570M bridge exploit", "coins": ["BNB"], "impact": "negative", "category": "hack"},
    {"date": "2022-10-11", "event": "Mango Markets exploited for $114M", "coins": ["MNGO", "SOL"], "impact": "negative", "category": "defi"},
    
    # 2023 Additional Events
    {"date": "2023-02-01", "event": "Optimism launches OP token airdrop", "coins": ["OP", "ETH"], "impact": "positive", "category": "defi"},
    {"date": "2023-03-02", "event": "Silvergate stock crashes 60% - crypto bank fears", "coins": ["BTC"], "impact": "negative", "category": "macro"},
    {"date": "2023-04-03", "event": "Arbitrum ARB token airdrop - $120M to users", "coins": ["ARB", "ETH"], "impact": "positive", "category": "defi"},
    {"date": "2023-05-05", "event": "Pepe memecoin launches - 400,000% gains in weeks", "coins": ["PEPE"], "impact": "positive", "category": "meme"},
    {"date": "2023-06-29", "event": "Bitcoin ordinals NFTs exceed 10M inscriptions", "coins": ["BTC"], "impact": "positive", "category": "technology"},
    {"date": "2023-07-06", "event": "Multichain bridge collapse - $130M frozen", "coins": ["MULTI"], "impact": "negative", "category": "defi"},
    {"date": "2023-08-16", "event": "PayPal launches PYUSD stablecoin", "coins": ["ETH"], "impact": "positive", "category": "institutional"},
    {"date": "2023-09-12", "event": "Friend.tech social token platform launches on Base", "coins": ["ETH"], "impact": "positive", "category": "defi"},
    {"date": "2023-10-04", "event": "Chainlink launches CCIP cross-chain protocol", "coins": ["LINK"], "impact": "positive", "category": "technology"},
    {"date": "2023-10-23", "event": "Bitcoin breaks $35,000 on ETF optimism", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2023-11-09", "event": "Sam Bankman-Fried found guilty on all charges", "coins": ["FTT", "SOL"], "impact": "mixed", "category": "regulatory"},
    {"date": "2023-12-11", "event": "Solana surges to $70 - 400% from 2023 lows", "coins": ["SOL"], "impact": "positive", "category": "milestone"},
    {"date": "2023-12-18", "event": "Ledger Connect Kit supply chain attack", "coins": ["ETH"], "impact": "negative", "category": "hack"},
    {"date": "2023-12-25", "event": "Bonk memecoin surges 600% in December", "coins": ["BONK", "SOL"], "impact": "positive", "category": "meme"},
    
    # 2024 Additional Events
    {"date": "2024-01-25", "event": "Grayscale GBTC outflows reach $5B post-ETF", "coins": ["BTC"], "impact": "negative", "category": "institutional"},
    {"date": "2024-02-07", "event": "Bitcoin breaks $45,000 on ETF momentum", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-02-29", "event": "Bitcoin surpasses $60,000 for first time since 2021", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    {"date": "2024-03-11", "event": "Dencun upgrade reduces L2 fees by 90%", "coins": ["ETH", "ARB", "OP"], "impact": "positive", "category": "technology"},
    {"date": "2024-03-27", "event": "BlackRock IBIT becomes largest Bitcoin ETF", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-04-13", "event": "Hong Kong approves spot Bitcoin and Ethereum ETFs", "coins": ["BTC", "ETH"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-05-01", "event": "Bitcoin drops 15% post-halving as sell-news event", "coins": ["BTC"], "impact": "negative", "category": "milestone"},
    {"date": "2024-05-23", "event": "SEC approves spot Ethereum ETF 19b-4 filings", "coins": ["ETH"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-06-04", "event": "Roaring Kitty returns - GameStop and memecoins surge", "coins": ["DOGE", "SHIB"], "impact": "positive", "category": "meme"},
    {"date": "2024-06-18", "event": "LayerZero ZRO token airdrop - $600M distribution", "coins": ["ZRO"], "impact": "positive", "category": "defi"},
    {"date": "2024-07-29", "event": "Trump speaks at Bitcoin Nashville conference", "coins": ["BTC"], "impact": "positive", "category": "regulatory"},
    {"date": "2024-08-25", "event": "Telegram TON token surges on chat integration", "coins": ["TON"], "impact": "positive", "category": "technology"},
    {"date": "2024-09-05", "event": "Bitcoin ETFs cross $50B total AUM", "coins": ["BTC"], "impact": "positive", "category": "institutional"},
    {"date": "2024-09-27", "event": "China stimulus announcement pumps risk assets", "coins": ["BTC", "ETH"], "impact": "positive", "category": "macro"},
    {"date": "2024-10-16", "event": "World Liberty Financial token launches - Trump family project", "coins": ["BTC"], "impact": "mixed", "category": "celebrity"},
    {"date": "2024-11-15", "event": "Dogecoin surges 150% on DOGE department memes", "coins": ["DOGE"], "impact": "positive", "category": "meme"},
    {"date": "2024-11-28", "event": "Bitcoin challenges $100,000 - fails at $98,500", "coins": ["BTC"], "impact": "mixed", "category": "milestone"},
    {"date": "2024-12-11", "event": "XRP surges to $2.50 - highest since 2018", "coins": ["XRP"], "impact": "positive", "category": "milestone"},
    {"date": "2024-12-24", "event": "Santa rally pushes Bitcoin above $100k again", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
    
    # 2025 Additional Projected Events
    {"date": "2025-02-05", "event": "Ethereum Prague-Electra upgrade scheduled", "coins": ["ETH"], "impact": "positive", "category": "technology"},
    {"date": "2025-02-08", "event": "Bitcoin recovers to $95,000 after tariff fears fade", "coins": ["BTC"], "impact": "positive", "category": "milestone"},
]

# Predictable event patterns identified from historical data
PREDICTABLE_PATTERNS = [
    {
        "pattern": "halving_cycle",
        "description": "Bitcoin halving every ~4 years reduces supply, historically followed by bull run",
        "predictability": "HIGH",
        "lead_time_days": 365,
        "next_occurrence": "2028-04-XX",
        "historical_impact": "+300-500% within 12-18 months post-halving",
        "coins": ["BTC"],
        "signals": ["Mining difficulty adjustments", "Block height approaching milestone"]
    },
    {
        "pattern": "etf_decision_dates",
        "description": "SEC has specific deadlines for ETF approvals - volatility expected",
        "predictability": "HIGH",
        "lead_time_days": 30,
        "next_occurrence": "Ongoing - check SEC calendar",
        "historical_impact": "+/- 5-15% on decision day",
        "coins": ["BTC", "ETH", "SOL"],
        "signals": ["SEC deadline calendars", "Amendment filings"]
    },
    {
        "pattern": "fomc_meetings",
        "description": "Fed rate decisions impact crypto - 8 meetings per year",
        "predictability": "HIGH",
        "lead_time_days": 45,
        "next_occurrence": "Check Fed calendar",
        "historical_impact": "+/- 3-10% depending on hawkish/dovish tone",
        "coins": ["BTC", "ETH"],
        "signals": ["CPI data", "Employment data", "Fed speeches"]
    },
    {
        "pattern": "major_upgrades",
        "description": "Ethereum upgrades, Bitcoin soft forks announced months ahead",
        "predictability": "HIGH",
        "lead_time_days": 90,
        "next_occurrence": "ETH Pectra upgrade 2025",
        "historical_impact": "+10-30% pre-upgrade, volatile post-upgrade",
        "coins": ["ETH", "BTC"],
        "signals": ["Developer announcements", "Testnet deployments"]
    },
    {
        "pattern": "quarterly_earnings",
        "description": "MicroStrategy, Coinbase, miners report quarterly - price catalyst",
        "predictability": "HIGH",
        "lead_time_days": 30,
        "next_occurrence": "Every quarter",
        "historical_impact": "+/- 5-15% for related assets",
        "coins": ["BTC"],
        "signals": ["Earnings calendars", "Pre-announcements"]
    },
    {
        "pattern": "token_unlocks",
        "description": "Large token unlocks create sell pressure - scheduled in advance",
        "predictability": "HIGH",
        "lead_time_days": 7,
        "next_occurrence": "Check token unlock calendars",
        "historical_impact": "-5-20% around unlock dates",
        "coins": ["SOL", "APT", "ARB", "OP"],
        "signals": ["TokenUnlocks.app", "Vesting schedules"]
    },
    {
        "pattern": "options_expiry",
        "description": "Large options expiries cause volatility - last Friday of month",
        "predictability": "HIGH",
        "lead_time_days": 7,
        "next_occurrence": "Monthly/Quarterly",
        "historical_impact": "Increased volatility +/- 5-10%",
        "coins": ["BTC", "ETH"],
        "signals": ["Open interest data", "Max pain price"]
    },
    {
        "pattern": "regulatory_calendar",
        "description": "Court cases, SEC deadlines, congressional hearings scheduled ahead",
        "predictability": "MEDIUM",
        "lead_time_days": 14,
        "next_occurrence": "Various - check legal calendars",
        "historical_impact": "+/- 10-30% depending on outcome",
        "coins": ["XRP", "BNB", "SOL"],
        "signals": ["Court calendars", "Congressional schedules"]
    },
    {
        "pattern": "seasonal_patterns",
        "description": "Q4 historically strongest, September historically weakest",
        "predictability": "MEDIUM",
        "lead_time_days": 30,
        "next_occurrence": "Annual cycle",
        "historical_impact": "Q4 avg +40%, Sep avg -5%",
        "coins": ["BTC", "ETH"],
        "signals": ["Historical data", "Tax-loss harvesting season"]
    },
    {
        "pattern": "celebrity_events",
        "description": "Elon Musk appearances, major interviews often trigger moves",
        "predictability": "LOW",
        "lead_time_days": 1,
        "next_occurrence": "Unpredictable",
        "historical_impact": "DOGE +/- 20-50%, BTC +/- 5-10%",
        "coins": ["DOGE", "BTC"],
        "signals": ["Social media monitoring", "Event announcements"]
    },
    {
        "pattern": "exchange_issues",
        "description": "Exchange hacks, insolvencies often have warning signs",
        "predictability": "LOW",
        "lead_time_days": 0,
        "next_occurrence": "Unpredictable",
        "historical_impact": "-10-30% market-wide",
        "coins": ["BTC", "ETH"],
        "signals": ["Withdrawal delays", "On-chain outflows", "Social media FUD"]
    },
]


class HistoricalEventsDatabase:
    """
    Downloads and stores historical crypto events.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, coindesk_service=None, correlation_engine=None):
        self.db = db
        self.coindesk_service = coindesk_service
        self.correlation_engine = correlation_engine
        self.events_collection = "historical_events"
        
    async def seed_major_events(self) -> Dict[str, Any]:
        """
        Seed the database with known major events.
        """
        inserted = 0
        updated = 0
        
        for event in MAJOR_EVENTS:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            doc = {
                "date": event["date"],
                "timestamp": int(event_date.timestamp()),
                "event": event["event"],
                "coins": event["coins"],
                "impact": event["impact"],
                "category": event["category"],
                "source": "curated",
                "is_major": True,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[self.events_collection].update_one(
                {"date": event["date"], "event": event["event"]},
                {"$set": doc},
                upsert=True
            )
            
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        
        # Create indexes
        await self.db[self.events_collection].create_index([("date", 1)])
        await self.db[self.events_collection].create_index([("coins", 1)])
        await self.db[self.events_collection].create_index([("category", 1)])
        await self.db[self.events_collection].create_index([("timestamp", 1)])
        
        return {
            "status": "success",
            "total_events": len(MAJOR_EVENTS),
            "inserted": inserted,
            "updated": updated
        }
    
    async def enrich_events_with_news(self, limit: int = 20) -> Dict[str, Any]:
        """
        Enrich stored events with actual news articles from CoinDesk.
        """
        if not self.coindesk_service:
            return {"error": "CoinDesk service not available"}
        
        # Get events without news enrichment
        events = await self.db[self.events_collection].find(
            {"news_enriched": {"$ne": True}},
            {"_id": 0}
        ).limit(limit).to_list(limit)
        
        enriched = 0
        
        for event in events:
            try:
                # Get news around the event date
                event_ts = event.get("timestamp", 0)
                if not event_ts:
                    continue
                
                to_ts = event_ts + 86400  # Next day
                
                result = await self.coindesk_service._request(
                    "/news/v1/article/list",
                    {"limit": 30, "to_ts": to_ts, "lang": "EN"}
                )
                
                related_news = []
                for article in result.get("Data", []):
                    pub_ts = article.get("PUBLISHED_ON", 0)
                    # Within 2 days of event
                    if event_ts - 86400 <= pub_ts <= event_ts + 86400:
                        title = article.get("TITLE", "").lower()
                        # Check relevance
                        event_words = event.get("event", "").lower().split()
                        if any(word in title for word in event_words if len(word) > 4):
                            related_news.append({
                                "title": article.get("TITLE"),
                                "url": article.get("URL"),
                                "sentiment": article.get("SENTIMENT"),
                                "published_at": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat()
                            })
                
                # Update event with news
                await self.db[self.events_collection].update_one(
                    {"date": event["date"], "event": event["event"]},
                    {
                        "$set": {
                            "news_enriched": True,
                            "related_news": related_news[:5],
                            "news_count": len(related_news),
                            "enriched_at": datetime.now(timezone.utc)
                        }
                    }
                )
                enriched += 1
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"Error enriching event {event.get('event')}: {e}")
                continue
        
        return {
            "status": "success",
            "events_processed": len(events),
            "events_enriched": enriched
        }
    
    async def add_price_impact(self) -> Dict[str, Any]:
        """
        Add price impact data to events by correlating with OHLCV data.
        """
        events = await self.db[self.events_collection].find(
            {"price_impact_calculated": {"$ne": True}},
            {"_id": 0}
        ).to_list(length=100)
        
        updated = 0
        
        for event in events:
            try:
                event_ts = event.get("timestamp", 0)
                coins = event.get("coins", [])
                
                if not event_ts or not coins:
                    continue
                
                price_impacts = {}
                
                for coin in coins:
                    # Get price data around event
                    data = await self.db.historical_ohlcv.find({
                        "symbol": coin.upper(),
                        "timestamp": {
                            "$gte": event_ts - 86400 * 3,  # 3 days before
                            "$lte": event_ts + 86400 * 7   # 7 days after
                        }
                    }, {"_id": 0}).sort("timestamp", 1).to_list(length=20)
                    
                    if len(data) >= 3:
                        # Find price before and after
                        before_prices = [d["close"] for d in data if d["timestamp"] < event_ts]
                        after_prices = [d["close"] for d in data if d["timestamp"] >= event_ts]
                        
                        if before_prices and after_prices:
                            price_before = before_prices[-1]
                            price_at_event = after_prices[0]
                            price_1d = after_prices[1] if len(after_prices) > 1 else price_at_event
                            price_7d = after_prices[-1]
                            
                            if price_before > 0:
                                price_impacts[coin] = {
                                    "price_before": round(price_before, 2),
                                    "price_at_event": round(price_at_event, 2),
                                    "price_1d_after": round(price_1d, 2),
                                    "price_7d_after": round(price_7d, 2),
                                    "change_immediate_pct": round(((price_at_event - price_before) / price_before) * 100, 2),
                                    "change_1d_pct": round(((price_1d - price_before) / price_before) * 100, 2),
                                    "change_7d_pct": round(((price_7d - price_before) / price_before) * 100, 2)
                                }
                
                if price_impacts:
                    await self.db[self.events_collection].update_one(
                        {"date": event["date"], "event": event["event"]},
                        {
                            "$set": {
                                "price_impact": price_impacts,
                                "price_impact_calculated": True
                            }
                        }
                    )
                    updated += 1
                    
            except Exception as e:
                print(f"Error calculating price impact for {event.get('event')}: {e}")
                continue
        
        return {
            "status": "success",
            "events_processed": len(events),
            "events_updated": updated
        }
    
    async def get_events(
        self,
        coin: str = None,
        category: str = None,
        impact: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Query events with filters.
        """
        query = {}
        
        if coin:
            query["coins"] = coin.upper()
        if category:
            query["category"] = category.lower()
        if impact:
            query["impact"] = impact.lower()
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        events = await self.db[self.events_collection].find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return events
    
    async def get_events_for_coin(self, coin: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all events affecting a specific coin"""
        return await self.get_events(coin=coin, limit=limit)
    
    async def get_events_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events by category (celebrity, regulatory, hack, etc.)"""
        return await self.get_events(category=category, limit=limit)
    
    async def search_events(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search events by keyword"""
        events = await self.db[self.events_collection].find(
            {"event": {"$regex": keyword, "$options": "i"}},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return events
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored events"""
        total = await self.db[self.events_collection].count_documents({})
        
        # Count by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_category = await self.db[self.events_collection].aggregate(pipeline).to_list(length=20)
        
        # Count by impact
        pipeline = [
            {"$group": {"_id": "$impact", "count": {"$sum": 1}}}
        ]
        by_impact = await self.db[self.events_collection].aggregate(pipeline).to_list(length=5)
        
        # Date range
        oldest = await self.db[self.events_collection].find_one(
            {}, {"date": 1}, sort=[("timestamp", 1)]
        )
        newest = await self.db[self.events_collection].find_one(
            {}, {"date": 1}, sort=[("timestamp", -1)]
        )
        
        return {
            "total_events": total,
            "by_category": {c["_id"]: c["count"] for c in by_category if c["_id"]},
            "by_impact": {i["_id"]: i["count"] for i in by_impact if i["_id"]},
            "date_range": {
                "oldest": oldest.get("date") if oldest else None,
                "newest": newest.get("date") if newest else None
            },
            "events_with_news": await self.db[self.events_collection].count_documents({"news_enriched": True}),
            "events_with_price_impact": await self.db[self.events_collection].count_documents({"price_impact_calculated": True})
        }
    
    def get_predictable_patterns(self) -> List[Dict[str, Any]]:
        """
        Get known predictable event patterns that can be anticipated.
        These are events with HIGH probability of occurring and known timing.
        """
        return PREDICTABLE_PATTERNS
    
    async def analyze_pattern_accuracy(self) -> Dict[str, Any]:
        """
        Analyze how accurate each pattern type has been historically.
        """
        results = {
            "patterns_analyzed": [],
            "summary": {}
        }
        
        # Analyze each pattern type from historical events
        pattern_analysis = {
            "halving": {
                "dates": ["2012-11-28", "2016-07-09", "2020-05-11", "2024-04-20"],
                "predicted_direction": "positive",
                "events_found": []
            },
            "etf_decisions": {
                "keywords": ["ETF"],
                "predicted_direction": "mixed",
                "events_found": []
            },
            "regulatory": {
                "keywords": ["SEC", "ban", "regulate", "legal"],
                "predicted_direction": "mixed", 
                "events_found": []
            },
            "celebrity": {
                "keywords": ["Elon", "Musk", "tweet"],
                "predicted_direction": "mixed",
                "events_found": []
            },
            "macro": {
                "keywords": ["Fed", "rate", "inflation", "recession"],
                "predicted_direction": "mixed",
                "events_found": []
            }
        }
        
        # Get all events
        all_events = await self.get_events(limit=200)
        
        for pattern_name, config in pattern_analysis.items():
            matching_events = []
            
            for event in all_events:
                event_text = event.get("event", "").lower()
                
                if "keywords" in config:
                    if any(kw.lower() in event_text for kw in config["keywords"]):
                        matching_events.append({
                            "date": event.get("date"),
                            "event": event.get("event"),
                            "impact": event.get("impact"),
                            "price_change": event.get("price_impact", {}).get("BTC", {}).get("change_7d_pct", 0)
                        })
                elif "dates" in config:
                    if event.get("date") in config["dates"]:
                        matching_events.append({
                            "date": event.get("date"),
                            "event": event.get("event"),
                            "impact": event.get("impact"),
                            "price_change": event.get("price_impact", {}).get("BTC", {}).get("change_7d_pct", 0)
                        })
            
            # Calculate accuracy
            correct_predictions = 0
            total_predictions = len(matching_events)
            
            for event in matching_events:
                impact = event.get("impact", "")
                predicted = config["predicted_direction"]
                
                if predicted == "mixed":
                    correct_predictions += 1  # Mixed means we predicted volatility
                elif predicted == impact:
                    correct_predictions += 1
            
            accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
            
            results["patterns_analyzed"].append({
                "pattern": pattern_name,
                "events_matched": total_predictions,
                "accuracy": round(accuracy, 1),
                "sample_events": matching_events[:3]
            })
        
        # Overall summary
        total_patterns = len(results["patterns_analyzed"])
        avg_accuracy = sum(p["accuracy"] for p in results["patterns_analyzed"]) / total_patterns if total_patterns > 0 else 0
        
        results["summary"] = {
            "total_patterns_analyzed": total_patterns,
            "average_accuracy": round(avg_accuracy, 1),
            "most_predictable": max(results["patterns_analyzed"], key=lambda x: x["accuracy"])["pattern"] if results["patterns_analyzed"] else None
        }
        
        return results
    
    async def get_upcoming_predictable_events(self) -> List[Dict[str, Any]]:
        """
        Get upcoming events that can be predicted based on known patterns.
        """
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        upcoming = []
        
        # Bitcoin halving - next one is 2028
        next_halving = datetime(2028, 4, 15, tzinfo=timezone.utc)
        days_until = (next_halving - now).days
        upcoming.append({
            "event_type": "Bitcoin Halving",
            "predicted_date": "2028-04-XX",
            "days_until": days_until,
            "predictability": "HIGH",
            "expected_impact": "positive",
            "historical_avg_impact": "+300-500% within 18 months",
            "coins_affected": ["BTC"],
            "preparation_signals": [
                "Monitor block height (every 210,000 blocks)",
                "Mining difficulty increases",
                "Miner accumulation patterns"
            ]
        })
        
        # FOMC meetings 2026 (8 meetings per year)
        fomc_2026 = [
            "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
            "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16"
        ]
        for fomc_date in fomc_2026:
            fomc_dt = datetime.strptime(fomc_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if fomc_dt > now:
                days_until = (fomc_dt - now).days
                upcoming.append({
                    "event_type": "FOMC Meeting",
                    "predicted_date": fomc_date,
                    "days_until": days_until,
                    "predictability": "HIGH",
                    "expected_impact": "mixed",
                    "historical_avg_impact": "+/- 3-10%",
                    "coins_affected": ["BTC", "ETH"],
                    "preparation_signals": [
                        "CPI data releases",
                        "Employment reports",
                        "Fed speaker comments"
                    ]
                })
        
        # US CPI releases (approx second Friday of month)
        cpi_2026 = [
            "2026-02-13", "2026-03-13", "2026-04-10", "2026-05-15",
            "2026-06-12", "2026-07-10", "2026-08-14", "2026-09-11",
            "2026-10-09", "2026-11-13", "2026-12-11"
        ]
        for cpi_date in cpi_2026:
            cpi_dt = datetime.strptime(cpi_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if cpi_dt > now:
                days_until = (cpi_dt - now).days
                upcoming.append({
                    "event_type": "US CPI Release",
                    "predicted_date": cpi_date,
                    "days_until": days_until,
                    "predictability": "HIGH",
                    "expected_impact": "mixed",
                    "historical_avg_impact": "+/- 3-8% intraday volatility",
                    "coins_affected": ["BTC", "ETH"],
                    "preparation_signals": [
                        "Consensus CPI estimates",
                        "Breakevens / inflation swaps",
                        "Dollar index moves"
                    ]
                })
        
        # US Non-Farm Payrolls (first Friday)
        nfp_2026 = [
            "2026-02-06", "2026-03-06", "2026-04-03", "2026-05-01",
            "2026-06-05", "2026-07-03", "2026-08-07", "2026-09-04",
            "2026-10-02", "2026-11-06", "2026-12-04"
        ]
        for nfp_date in nfp_2026:
            nfp_dt = datetime.strptime(nfp_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if nfp_dt > now:
                days_until = (nfp_dt - now).days
                upcoming.append({
                    "event_type": "US Non-Farm Payrolls",
                    "predicted_date": nfp_date,
                    "days_until": days_until,
                    "predictability": "HIGH",
                    "expected_impact": "mixed",
                    "historical_avg_impact": "+/- 2-6% intraday volatility",
                    "coins_affected": ["BTC", "ETH"],
                    "preparation_signals": [
                        "ADP employment preview",
                        "Jobless claims trends",
                        "Fed speaker tone before print"
                    ]
                })
        
        # Options expiry (last Friday of each month)
        current_month = now.month
        current_year = now.year
        for month_offset in range(0, 6):
            month = (current_month + month_offset - 1) % 12 + 1
            year = current_year if month >= current_month else current_year + 1
            
            # Find last Friday
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            last_date = datetime(year, month, last_day, tzinfo=timezone.utc)
            while last_date.weekday() != 4:  # Friday = 4
                last_date -= timedelta(days=1)
            
            if last_date > now:
                days_until = (last_date - now).days
                upcoming.append({
                    "event_type": "Options Expiry",
                    "predicted_date": last_date.strftime("%Y-%m-%d"),
                    "days_until": days_until,
                    "predictability": "HIGH",
                    "expected_impact": "mixed",
                    "historical_avg_impact": "+/- 5-10% volatility",
                    "coins_affected": ["BTC", "ETH"],
                    "preparation_signals": [
                        "Open interest levels",
                        "Max pain price",
                        "Put/Call ratio"
                    ]
                })
        
        # Quarterly earnings - next quarters
        earnings_dates = [
            {"date": "2026-02-15", "company": "MicroStrategy Q4 2025"},
            {"date": "2026-02-27", "company": "Coinbase Q4 2025"},
            {"date": "2026-05-01", "company": "MicroStrategy Q1 2026"},
            {"date": "2026-05-08", "company": "Coinbase Q1 2026"},
        ]
        for earning in earnings_dates:
            earn_dt = datetime.strptime(earning["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if earn_dt > now:
                days_until = (earn_dt - now).days
                upcoming.append({
                    "event_type": f"Earnings: {earning['company']}",
                    "predicted_date": earning["date"],
                    "days_until": days_until,
                    "predictability": "HIGH",
                    "expected_impact": "mixed",
                    "historical_avg_impact": "+/- 5-15%",
                    "coins_affected": ["BTC"],
                    "preparation_signals": [
                        "Pre-earnings guidance",
                        "Analyst estimates",
                        "Bitcoin treasury holdings"
                    ]
                })
        
        # Sort by days until
        upcoming.sort(key=lambda x: x["days_until"])
        
        return upcoming[:15]  # Return next 15 events


# Global instance
_events_db = None

def get_historical_events_db(db: AsyncIOMotorDatabase = None, coindesk_service=None, correlation_engine=None):
    """Get or create historical events database instance"""
    global _events_db
    if _events_db is None and db is not None:
        _events_db = HistoricalEventsDatabase(db, coindesk_service, correlation_engine)
    return _events_db
