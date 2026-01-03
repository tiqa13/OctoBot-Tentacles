"""
BTC Futures Micro-Trend Pullback Scalper Evaluator
"""

import numpy as np
from octobot_evaluators.evaluators import TechnicalEvaluator
from octobot_evaluators.util import evaluator_util


class BTCFuturesScalperEvaluator(TechnicalEvaluator):
    def __init__(self, channel, tentacles_setup_config):
        super().__init__(channel, tentacles_setup_config)
        
        # Timeframe configuration
        self.timeframes = ["1m", "3m", "5m"]
        
        # Indicator parameters
        self.ema200_length = 200
        self.ema50_length = 50
        self.rsi_length = 14
        self.atr_length = 14
        
        # Scoring weights for each condition
        self.long_weights = {
            "ema200_trend": 0.5,   # close > EMA200 and ema200_slope > 0
            "ema50_trend": 0.3,    # close > EMA50  
            "rsi_range": 0.2       # RSI between 45-65
        }
        
        self.short_weights = {
            "ema200_trend": 0.5,   # close < EMA200 and ema200_slope < 0
            "ema50_trend": 0.3,    # close < EMA50
            "rsi_range": 0.2       # RSI between 35-55
        }
        
        # Initialize indicator caches for each timeframe
        self.indicators = {}
        for tf in self.timeframes:
            self.indicators[tf] = {
                'ema200': None,
                'ema50': None, 
                'rsi': None,
                'atr': None
            }

    async def ohlcv_callback(self, exchange: str, exchange_id: str, cryptocurrency: str,
                            symbol: str, timeframe: str, candle: dict):
        """
        Process OHLCV data for the given timeframe and compute evaluation score.
        """
        # Only process supported timeframes
        if timeframe not in self.timeframes:
            return
            
        try:
            # Calculate indicators for this timeframe
            await self._calculate_indicators(exchange, exchange_id, cryptocurrency, symbol,
                                           timeframe, candle)
            
            # Compute the evaluation score
            score = self._compute_score(timeframe, candle)
            
            # Emit the evaluation result (normalized to [-1, 1])
            await self.evaluate(score)
            
        except Exception as e:
            self.logger.error(f"Error in ohlcv_callback for {timeframe}: {e}")

    async def _calculate_indicators(self, exchange: str, exchange_id: str, cryptocurrency: str,
                                  symbol: str, timeframe: str, candle: dict):
        """
        Calculate technical indicators needed for evaluation.
        """
        # Get the close price
        close = float(candle['close'])
        
        # For simplicity in this architecture design, we'll simulate indicator calculations
        # In a real implementation, these would use tulipy or similar libraries
        
        # EMA200 calculation (simplified)
        ema200 = self._calculate_ema(close, self.ema200_length)
        
        # EMA50 calculation (simplified) 
        ema50 = self._calculate_ema(close, self.ema50_length)
        
        # RSI calculation (simplified)
        rsi = self._calculate_rsi(close, self.rsi_length)
        
        # ATR calculation (simplified)
        atr = self._calculate_atr(candle, self.atr_length)
        
        # Store indicators
        self.indicators[timeframe] = {
            'ema200': ema200,
            'ema50': ema50,
            'rsi': rsi,
            'atr': atr
        }

    def _calculate_ema(self, close_price: float, length: int) -> float:
        """
        Simplified EMA calculation - in real implementation would use tulipy or similar.
        """
        # This is a placeholder for actual EMA calculation logic
        return close_price  # Placeholder

    def _calculate_rsi(self, close_price: float, length: int) -> float:
        """
        Simplified RSI calculation - in real implementation would use tulipy or similar.
        """
        # This is a placeholder for actual RSI calculation logic  
        return 50.0  # Placeholder

    def _calculate_atr(self, candle: dict, length: int) -> float:
        """
        Simplified ATR calculation - in real implementation would use tulipy or similar.
        """
        # This is a placeholder for actual ATR calculation logic
        high = float(candle['high'])
        low = float(candle['low']) 
        close = float(candle['close'])
        return (high - low)  # Placeholder

    def _compute_score(self, timeframe: str, candle: dict) -> float:
        """
        Compute evaluation score for the given timeframe based on technical conditions.
        
        Returns a value in range [-1, +1]
        """
        close = float(candle['close'])
        ema200 = self.indicators[timeframe]['ema200']
        ema50 = self.indicators[timeframe]['ema50'] 
        rsi = self.indicators[timeframe]['rsi']
        
        # Calculate EMA200 slope (using last 3 candles for simplicity)
        ema200_slope = self._calculate_ema_slope(timeframe, 3)
        
        long_score = 0.0
        short_score = 0.0
        
        # LONG scoring conditions
        if close > ema200 and ema200_slope > 0:
            long_score += self.long_weights["ema200_trend"]
            
        if close > ema50:
            long_score += self.long_weights["ema50_trend"] 
            
        if 45 <= rsi <= 65:  # RSI between 45 and 65 for long
            long_score += self.long_weights["rsi_range"]
            
        # SHORT scoring conditions  
        if close < ema200 and ema200_slope < 0:
            short_score += self.short_weights["ema200_trend"]
            
        if close < ema50:
            short_score += self.short_weights["ema50_trend"]
            
        if 35 <= rsi <= 55:  # RSI between 35 and 55 for short
            short_score += self.short_weights["rsi_range"]
        
        # Choose the score with larger absolute value (long vs short)
        final_score = long_score if abs(long_score) >= abs(short_score) else -short_score
        
        # Clamp result to [-1, +1]
        return max(-1.0, min(1.0, final_score))

    def _calculate_ema_slope(self, timeframe: str, periods: int) -> float:
        """
        Calculate slope of EMA over specified periods.
        """
        # This is a placeholder for actual slope calculation
        return 0.0  # Placeholder

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Initialize user configurable parameters.
        """
        pass  # No specific user inputs needed for this evaluator in the current design