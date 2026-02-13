"""
Whale Wallet Tracking Service
=============================
Monitor large wallet movements on Ethereum blockchain using Etherscan API.
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WhaleTransaction:
    """A whale transaction"""
    hash: str
    from_address: str
    to_address: str
    value_eth: float
    value_usd: float
    token_symbol: str
    block_number: int
    timestamp: str
    direction: str  # 'in', 'out', 'transfer'
    is_exchange: bool
    exchange_name: Optional[str] = None


@dataclass 
class WatchedWallet:
    """A wallet being watched"""
    address: str
    label: str
    is_exchange: bool
    last_balance_eth: float
    last_checked: str


class WhaleTrackingService:
    """
    Whale wallet tracking service using Etherscan API.
    
    Features:
    - Monitor known whale wallets
    - Detect large transactions
    - Track exchange flows (in/out)
    - Alert on significant movements
    """
    
    # Etherscan API (free tier: 5 calls/sec, 100k calls/day)
    ETHERSCAN_API = "https://api.etherscan.io/api"
    
    # Known exchange wallets (partial list)
    EXCHANGE_WALLETS = {
        '0x28c6c06298d514db089934071355e5743bf21d60': 'Binance',
        '0x21a31ee1afc51d94c2efccaa2092ad1028285549': 'Binance',
        '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance',
        '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': 'Binance',
        '0x9696f59e4d72e237be84ffd425dcad154bf96976': 'Binance',
        '0x4976a4a02f38326660d17bf34b431dc6e2eb2327': 'Binance',
        '0xf977814e90da44bfa03b6295a0616a897441acec': 'Binance',
        '0x503828976d22510aad0201ac7ec88293211d23da': 'Coinbase',
        '0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740': 'Coinbase',
        '0x3cd751e6b0078be393132286c442345e5dc49699': 'Coinbase',
        '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511': 'Coinbase',
        '0xeb2629a2734e272bcc07bda959863f316f4bd4cf': 'Coinbase',
        '0x2910543af39aba0cd09dbb2d50200b3e800a63d2': 'Kraken',
        '0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13': 'Kraken',
        '0xe853c56864a2ebe4576a807d26fdc4a0ada51919': 'Kraken',
        '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': 'Kraken',
        '0xfa52274dd61e1643d2205169732f29114bc240b3': 'Kraken',
        '0x1151314c646ce4e0efd76d1af4760ae66a9fe30f': 'Bitfinex',
        '0x742d35cc6634c0532925a3b844bc454e4438f44e': 'Bitfinex',
        '0x876eabf441b2ee5b5b0554fd502a8e0600950cfa': 'Bitfinex',
        '0xdc76cd25977e0a5ae17155770273ad58648900d3': 'FTX (Bankrupt)',
        '0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2': 'FTX (Bankrupt)',
    }
    
    # Known whale wallets to monitor
    WHALE_WALLETS = [
        {'address': '0x00000000219ab540356cbb839cbe05303d7705fa', 'label': 'ETH2 Deposit Contract'},
        {'address': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'label': 'WETH Contract'},
        {'address': '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8', 'label': 'Binance Cold Wallet'},
        {'address': '0x40b38765696e3d5d8d9d834d8aad4bb6e418e489', 'label': 'Robinhood'},
        {'address': '0x1b3cb81e51011b549d78bf720b0d924ac763a7c2', 'label': 'Grayscale'},
    ]
    
    # Minimum ETH for whale alert
    MIN_WHALE_ETH = 100  # 100 ETH minimum
    
    def __init__(self, db, api_key: str = None):
        self.db = db
        self.api_key = api_key or ""  # Free tier works without key for basic queries
        self.watched_wallets: Dict[str, WatchedWallet] = {}
        self.recent_transactions: List[WhaleTransaction] = []
        self.is_monitoring = False
        self._monitor_task = None
        self.eth_price_usd = 2000  # Default, will be updated
        self.settings = {
            'min_whale_eth': self.MIN_WHALE_ETH,
            'check_interval_sec': 60,
            'max_transactions': 100,
            'alert_on_exchange_flow': True
        }
        logger.info("✅ Whale Tracking Service initialized")
    
    async def start_monitoring(self):
        """Start whale monitoring"""
        if self.is_monitoring:
            return {'status': 'already_running'}
        
        # Initialize watched wallets
        await self._init_watched_wallets()
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"🐋 Whale monitoring started ({len(self.watched_wallets)} wallets)")
        return {'status': 'started', 'wallets_watched': len(self.watched_wallets)}
    
    async def stop_monitoring(self):
        """Stop whale monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        return {'status': 'stopped'}
    
    async def _init_watched_wallets(self):
        """Initialize wallets to watch"""
        for wallet in self.WHALE_WALLETS:
            self.watched_wallets[wallet['address'].lower()] = WatchedWallet(
                address=wallet['address'].lower(),
                label=wallet['label'],
                is_exchange=wallet['address'].lower() in self.EXCHANGE_WALLETS,
                last_balance_eth=0,
                last_checked=datetime.now(timezone.utc).isoformat()
            )
        
        # Add exchange wallets
        for addr, name in self.EXCHANGE_WALLETS.items():
            if addr.lower() not in self.watched_wallets:
                self.watched_wallets[addr.lower()] = WatchedWallet(
                    address=addr.lower(),
                    label=name,
                    is_exchange=True,
                    last_balance_eth=0,
                    last_checked=datetime.now(timezone.utc).isoformat()
                )
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update ETH price
                await self._update_eth_price()
                
                # Check recent large transactions
                await self._check_large_transactions()
                
                # Check watched wallets
                await self._check_watched_wallets()
                
                await asyncio.sleep(self.settings['check_interval_sec'])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(30)
    
    async def _update_eth_price(self):
        """Update current ETH price"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.eth_price_usd = data.get('ethereum', {}).get('usd', 2000)
        except Exception as e:
            logger.debug(f"Failed to update ETH price: {e}")
    
    async def _check_large_transactions(self):
        """Check for recent large ETH transactions"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get latest blocks
                params = {
                    'module': 'proxy',
                    'action': 'eth_blockNumber',
                    'apikey': self.api_key
                }
                
                async with session.get(self.ETHERSCAN_API, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('result'):
                            latest_block = int(data['result'], 16)
                            
                            # Check transactions in recent blocks
                            await self._scan_block_for_whales(session, latest_block)
                            
        except Exception as e:
            logger.error(f"Check large transactions error: {e}")
    
    async def _scan_block_for_whales(self, session, block_number: int):
        """Scan a block for whale transactions"""
        try:
            params = {
                'module': 'proxy',
                'action': 'eth_getBlockByNumber',
                'tag': hex(block_number),
                'boolean': 'true',
                'apikey': self.api_key
            }
            
            async with session.get(self.ETHERSCAN_API, params=params, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    block = data.get('result', {})
                    
                    if not block or not block.get('transactions'):
                        return
                    
                    for tx in block.get('transactions', []):
                        value_wei = int(tx.get('value', '0'), 16)
                        value_eth = value_wei / 1e18
                        
                        if value_eth >= self.settings['min_whale_eth']:
                            await self._process_whale_transaction(tx, value_eth, block)
                            
        except Exception as e:
            logger.debug(f"Block scan error: {e}")
    
    async def _process_whale_transaction(self, tx: Dict, value_eth: float, block: Dict):
        """Process a detected whale transaction"""
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower() if tx.get('to') else ''
        
        # Determine direction relative to exchanges
        from_is_exchange = from_addr in self.EXCHANGE_WALLETS
        to_is_exchange = to_addr in self.EXCHANGE_WALLETS
        
        if from_is_exchange and not to_is_exchange:
            direction = 'out'  # Withdrawal from exchange
            exchange_name = self.EXCHANGE_WALLETS.get(from_addr)
        elif to_is_exchange and not from_is_exchange:
            direction = 'in'  # Deposit to exchange
            exchange_name = self.EXCHANGE_WALLETS.get(to_addr)
        else:
            direction = 'transfer'
            exchange_name = None
        
        whale_tx = WhaleTransaction(
            hash=tx.get('hash', ''),
            from_address=from_addr,
            to_address=to_addr,
            value_eth=value_eth,
            value_usd=value_eth * self.eth_price_usd,
            token_symbol='ETH',
            block_number=int(block.get('number', '0'), 16),
            timestamp=datetime.fromtimestamp(
                int(block.get('timestamp', '0'), 16),
                tz=timezone.utc
            ).isoformat(),
            direction=direction,
            is_exchange=from_is_exchange or to_is_exchange,
            exchange_name=exchange_name
        )
        
        # Add to recent transactions (avoid duplicates)
        existing = [t for t in self.recent_transactions if t.hash == whale_tx.hash]
        if not existing:
            self.recent_transactions.insert(0, whale_tx)
            self.recent_transactions = self.recent_transactions[:self.settings['max_transactions']]
            
            # Store in database
            await self.db.whale_transactions.insert_one(asdict(whale_tx))
            
            logger.info(f"🐋 Whale TX: {value_eth:.2f} ETH (${value_eth * self.eth_price_usd:,.0f}) - {direction}")
    
    async def _check_watched_wallets(self):
        """Check balances of watched wallets"""
        # Limit API calls - check a subset each iteration
        wallets_to_check = list(self.watched_wallets.values())[:5]
        
        for wallet in wallets_to_check:
            try:
                await self._check_wallet_balance(wallet)
                await asyncio.sleep(0.2)  # Rate limiting
            except Exception as e:
                logger.debug(f"Wallet check error {wallet.address[:10]}: {e}")
    
    async def _check_wallet_balance(self, wallet: WatchedWallet):
        """Check balance of a single wallet"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': wallet.address,
                    'tag': 'latest',
                    'apikey': self.api_key
                }
                
                async with session.get(self.ETHERSCAN_API, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == '1':
                            balance_wei = int(data.get('result', '0'))
                            balance_eth = balance_wei / 1e18
                            
                            # Check for significant change
                            if wallet.last_balance_eth > 0:
                                change = balance_eth - wallet.last_balance_eth
                                if abs(change) >= self.settings['min_whale_eth']:
                                    direction = 'in' if change > 0 else 'out'
                                    logger.info(f"🐋 {wallet.label}: {change:+.2f} ETH ({direction})")
                            
                            wallet.last_balance_eth = balance_eth
                            wallet.last_checked = datetime.now(timezone.utc).isoformat()
                            
        except Exception as e:
            logger.debug(f"Balance check error: {e}")
    
    async def add_wallet(self, address: str, label: str) -> Dict[str, Any]:
        """Add a wallet to watch"""
        address = address.lower()
        
        if not address.startswith('0x') or len(address) != 42:
            return {'status': 'error', 'message': 'Invalid Ethereum address'}
        
        self.watched_wallets[address] = WatchedWallet(
            address=address,
            label=label,
            is_exchange=address in self.EXCHANGE_WALLETS,
            last_balance_eth=0,
            last_checked=datetime.now(timezone.utc).isoformat()
        )
        
        # Store in database
        await self.db.watched_wallets.update_one(
            {'address': address},
            {'$set': {'address': address, 'label': label}},
            upsert=True
        )
        
        return {'status': 'success', 'address': address, 'label': label}
    
    async def remove_wallet(self, address: str) -> Dict[str, Any]:
        """Remove a wallet from watch list"""
        address = address.lower()
        
        if address in self.watched_wallets:
            del self.watched_wallets[address]
            await self.db.watched_wallets.delete_one({'address': address})
            return {'status': 'success'}
        
        return {'status': 'error', 'message': 'Wallet not found'}
    
    async def get_recent_transactions(self, limit: int = 50) -> List[Dict]:
        """Get recent whale transactions"""
        return [asdict(tx) for tx in self.recent_transactions[:limit]]
    
    async def get_watched_wallets(self) -> List[Dict]:
        """Get all watched wallets"""
        return [asdict(w) for w in self.watched_wallets.values()]
    
    async def get_exchange_flows(self, hours: int = 24) -> Dict[str, Any]:
        """Get exchange in/out flows for the past N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        inflows = sum(
            tx.value_eth for tx in self.recent_transactions
            if tx.direction == 'in' and tx.timestamp > cutoff.isoformat()
        )
        outflows = sum(
            tx.value_eth for tx in self.recent_transactions
            if tx.direction == 'out' and tx.timestamp > cutoff.isoformat()
        )
        
        return {
            'period_hours': hours,
            'inflows_eth': inflows,
            'inflows_usd': inflows * self.eth_price_usd,
            'outflows_eth': outflows,
            'outflows_usd': outflows * self.eth_price_usd,
            'net_flow_eth': outflows - inflows,  # Positive = more leaving exchanges (bullish)
            'net_flow_usd': (outflows - inflows) * self.eth_price_usd,
            'signal': 'bullish' if outflows > inflows else 'bearish' if inflows > outflows else 'neutral'
        }
    
    async def get_history(self, limit: int = 100) -> List[Dict]:
        """Get whale transaction history from database"""
        cursor = self.db.whale_transactions.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'is_monitoring': self.is_monitoring,
            'wallets_watched': len(self.watched_wallets),
            'recent_transactions': len(self.recent_transactions),
            'eth_price_usd': self.eth_price_usd,
            'settings': self.settings,
            'exchanges_tracked': len(self.EXCHANGE_WALLETS)
        }


# Singleton
_whale_service: Optional[WhaleTrackingService] = None


def get_whale_service(db=None, api_key: str = None) -> Optional[WhaleTrackingService]:
    """Get or create the whale tracking service"""
    global _whale_service
    if _whale_service is None and db is not None:
        _whale_service = WhaleTrackingService(db, api_key)
    return _whale_service
