import math
import tulipy
import numpy
import octobot_commons.constants as commons_constants
import octobot_evaluators.evaluators as evaluators
import octobot_evaluators.util as evaluators_util
import octobot_trading.api as trading_api


class RangeRegimeEvaluator15m(evaluators.TAEvaluator):
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.pertinence = 1
        # EMA periods for regime detection
        self.ema_short_period = 50
        self.ema_long_period = 200
        # ADX period
        self.adx_period = 14
        # ADX threshold for trend strength
        self.adx_threshold = 20

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the evaluator, should define all the evaluator's user inputs
        """
        self.ema_short_period = self.UI.user_input(
            "ema_short_period", 
            enums.UserInputTypes.INT, 
            self.ema_short_period,
            inputs,
            min_val=1,
            title="EMA Short Period: EMA period for short-term trend analysis"
        )
        
        self.ema_long_period = self.UI.user_input(
            "ema_long_period", 
            enums.UserInputTypes.INT, 
            self.ema_long_period,
            inputs,
            min_val=1,
            title="EMA Long Period: EMA period for long-term trend analysis"
        )
        
        self.adx_period = self.UI.user_input(
            "adx_period", 
            enums.UserInputTypes.INT, 
            self.adx_period,
            inputs,
            min_val=1,
            title="ADX Period: ADX period for trend strength measurement"
        )
        
        self.adx_threshold = self.UI.user_input(
            "adx_threshold", 
            enums.UserInputTypes.INT, 
            self.adx_threshold,
            inputs,
            min_val=0,
            title="ADX Threshold: ADX value below which regime is considered range (default 20)"
        )

    async def ohlcv_callback(self, exchange: str, exchange_id: str,
                             cryptocurrency: str, symbol: str, time_frame, candle, inc_in_construction_data):
        symbol_candles = self.get_exchange_symbol_data(exchange, exchange_id, symbol)
        close_candles = trading_api.get_symbol_close_candles(symbol_candles, time_frame,
                                                              include_in_construction=inc_in_construction_data)
        high_candles = trading_api.get_symbol_high_candles(symbol_candles, time_frame,
                                                            include_in_construction=inc_in_construction_data)
        low_candles = trading_api.get_symbol_low_candles(symbol_candles, time_frame,
                                                          include_in_construction=inc_in_construction_data)
        
        await self.evaluate(cryptocurrency, symbol, time_frame, close_candles, high_candles, low_candles, candle)

    async def evaluate(self, cryptocurrency, symbol, time_frame, close_candles, high_candles, low_candles, candle):
        # Initialize evaluation note
        self.eval_note = 0
        
        # Check if we have enough data for all indicators
        min_data_length = max(self.ema_short_period, self.ema_long_period, self.adx_period + 12)
        
        if len(close_candles) >= min_data_length:
            # Calculate EMA values
            ema_short = tulipy.ema(close_candles, self.ema_short_period)
            ema_long = tulipy.ema(close_candles, self.ema_long_period)
            
            # Calculate ADX value
            adx = tulipy.adx(high_candles, low_candles, close_candles, self.adx_period)
            
            # Remove NaN values from the end of arrays (tulipy may return some NaNs at beginning)
            ema_short_clean = [val for val in ema_short if not math.isnan(val)]
            ema_long_clean = [val for val in ema_long if not math.isnan(val)]
            adx_clean = [val for val in adx if not math.isnan(val)]
            
            # Check if we have enough clean data
            if len(ema_short_clean) >= 2 and len(ema_long_clean) >= 2 and len(adx_clean) >= 1:
                # Get the latest values
                current_ema_short = ema_short_clean[-1]
                previous_ema_short = ema_short_clean[-2] 
                current_ema_long = ema_long_clean[-1]
                previous_ema_long = ema_long_clean[-2]
                current_adx = adx_clean[-1]
                
                # Check if price oscillates around EMA50 (flat trend)
                # Calculate slope of EMA50
                ema_slope = current_ema_short - previous_ema_short
                
                # Check ADX value for weak trend
                adx_weak_trend = current_adx < self.adx_threshold
                
                # If we're in a range regime, return +1 (enabled)
                # Otherwise return 0 (disabled)
                if adx_weak_trend and abs(ema_slope) < (current_ema_short * 0.02):  # Flat EMA slope
                    self.eval_note = 1
                else:
                    self.eval_note = 0
                    
        await self.evaluation_completed(cryptocurrency, symbol, time_frame,
                                        eval_time=evaluators_util.get_eval_time(full_candle=candle,
                                                                                time_frame=time_frame))

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        """
        :return: True if the evaluator is not symbol dependant else False
        """
        return False

    @classmethod
    def get_is_time_frame_wildcard(cls) -> bool:
        """
        :return: True if the evaluator is not time_frame dependant else False
        """
        return False
