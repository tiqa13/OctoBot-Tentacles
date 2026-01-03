"""
BTC Futures Micro-Trend Pullback Scalper Strategy
"""

from octobot_trading.strategies import StrategyEvaluator
from octobot_trading.enums import TradeType


class BTCFuturesScalperStrategy(StrategyEvaluator):
    def __init__(self, channel, tentacles_setup_config):
        super().__init__(channel, tentacles_setup_config)
        
        # Timeframe weights for evaluation scores
        self.timeframe_weights = {
            "1m": 0.50,
            "3m": 0.30, 
            "5m": 0.20
        }
        
        # Trading thresholds
        self.long_threshold = 0.60
        self.short_threshold = -0.60
        
        # Store evaluator results for each timeframe
        self.evaluator_results = {}
        
        # Track previous signal to prevent flip during same candle
        self.previous_signal = None

    async def matrix_callback(self, exchange: str, exchange_id: str, cryptocurrency: str,
                            symbol: str, timeframe: str, matrix: dict):
        """
        Process evaluation results from the technical evaluator.
        """
        # Store the result for this timeframe
        if timeframe in self.timeframe_weights:
            self.evaluator_results[timeframe] = matrix
            
        # If we have all timeframes, compute final signal
        if len(self.evaluator_results) == 3:  # We have results from all 3 timeframes
            await self._compute_final_signal(cryptocurrency, symbol)

    async def _compute_final_signal(self, cryptocurrency: str, symbol: str):
        """
        Compute weighted average of evaluator scores and determine final signal.
        """
        try:
            # Get scores for each timeframe (assuming they're in the matrix)
            scores = []
            for tf, weight in self.timeframe_weights.items():
                if tf in self.evaluator_results:
                    # Extract score from the evaluation result
                    # In a real implementation this would be more sophisticated
                    score = self._extract_score_from_matrix(self.evaluator_results[tf])
                    weighted_score = score * weight
                    scores.append(weighted_score)
            
            # Compute final weighted signal
            if scores:
                final_signal = sum(scores)
                
                # Apply trading thresholds
                if final_signal >= self.long_threshold:
                    await self._emit_long_signal(cryptocurrency, symbol)
                elif final_signal <= self.short_threshold:
                    await self._emit_short_signal(cryptocurrency, symbol)
                else:
                    await self._emit_neutral_signal(cryptocurrency, symbol)
                    
        except Exception as e:
            self.logger.error(f"Error in _compute_final_signal: {e}")

    def _extract_score_from_matrix(self, matrix: dict) -> float:
        """
        Extract evaluation score from the matrix data structure.
        This is a placeholder - actual implementation would depend on OctoBot's matrix format.
        """
        # In a real implementation this would extract the actual score
        # For now we'll return 0.0 as a placeholder
        return 0.0

    async def _emit_long_signal(self, cryptocurrency: str, symbol: str):
        """
        Emit LONG signal to trading mode.
        """
        await self._emit_signal(TradeType.BUY, cryptocurrency, symbol)

    async def _emit_short_signal(self, cryptocurrency: str, symbol: str):
        """
        Emit SHORT signal to trading mode.
        """
        await self._emit_signal(TradeType.SELL, cryptocurrency, symbol)
        
    async def _emit_neutral_signal(self, cryptocurrency: str, symbol: str):
        """
        Emit NEUTRAL signal (no trade).
        """
        # For now we'll emit a neutral signal but in practice this might be handled differently
        pass

    async def _emit_signal(self, trade_type: TradeType, cryptocurrency: str, symbol: str):
        """
        Emit the actual trading signal.
        """
        try:
            # Check if signal has flipped during same candle (safety check)
            current_signal = "LONG" if trade_type == TradeType.BUY else "SHORT"
            if self.previous_signal is not None and self.previous_signal == current_signal:
                # Same direction, no flip - proceed
                pass
            elif self.previous_signal is not None:
                # Signal flipped during same candle - skip to avoid conflicts
                return
                
            self.previous_signal = current_signal
            
            # Emit the signal (this would be handled by OctoBot's trading system)
            await self.trigger_signal(trade_type, cryptocurrency, symbol)
            
        except Exception as e:
            self.logger.error(f"Error emitting signal: {e}")

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Initialize user configurable parameters.
        """
        # No specific user inputs needed for this strategy in the current design
        pass

    async def trigger_signal(self, trade_type: TradeType, cryptocurrency: str, symbol: str):
        """
        Trigger actual trading signal (placeholder).
        This would be implemented by OctoBot's framework.
        """
        pass