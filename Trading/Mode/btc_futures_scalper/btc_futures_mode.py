"""
BTC Futures Micro-Trend Pullback Scalper Trading Mode
"""

from octobot_trading.modes import TradingMode
from octobot_trading.enums import ExchangeTypes


class BTCFuturesScalperMode(TradingMode):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        
        # Define supported exchanges and trading pairs for futures
        self.supported_exchanges = [
            "bybit", 
            "binance_futures",
            "kucoin_futures"
        ]
        
        # Supported trading pairs (BTC/USDT perpetual futures)
        self.supported_pairs = ["BTC/USDT"]
        
        # Timeframes to use for evaluation
        self.timeframes = ["1m", "3m", "5m"]

    async def create_producers(self):
        """
        Create producers for this trading mode.
        """
        # In a real implementation, this would set up the necessary producers 
        # that feed data into our strategy and evaluator
        
        # For now we'll just call the parent method
        await super().create_producers()

    async def create_consumers(self):
        """
        Create consumers for this trading mode.
        """
        # In a real implementation, this would set up the necessary consumers 
        # that process signals from our strategy and execute trades
        
        # For now we'll just call the parent method
        await super().create_consumers()

    def get_supported_exchange_types(self):
        """
        Return list of supported exchange types for futures trading.
        """
        return [
            ExchangeTypes.FUTURE,
            ExchangeTypes.PERPETUAL_FUTURE
        ]

    async def start(self):
        """
        Start the trading mode.
        """
        # Initialize any required components
        await super().start()
        
        self.logger.info("BTC Futures Micro-Trend Pullback Scalper Mode started")

    def get_required_evaluators(self):
        """
        Return list of evaluators needed by this trading mode.
        """
        return ["btc_futures_scalper"]

    def get_required_strategies(self):
        """
        Return list of strategies needed by this trading mode.
        """
        return ["btc_futures_scalper"]