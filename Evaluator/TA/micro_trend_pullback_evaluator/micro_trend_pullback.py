import math
import numpy as np
import tulipy
import typing

import octobot_commons.constants as commons_constants
import octobot_commons.enums as enums
import octobot_commons.data_util as data_util
import octobot_evaluators.evaluators as evaluators
import octobot_evaluators.util as evaluators_util
import octobot_trading.api as trading_api
import tentacles.Evaluator.Util as EvaluatorUtil


class MicroTrendPullbackEvaluator(evaluators.TAEvaluator):
    """
    Custom evaluator for BTC Micro-Trend Pullback system.
    
    This evaluator identifies micro-trends in BTC price movements and detects 
    potential pullbacks that could indicate entry points for trading strategies.
    
    It analyzes:
    - Short-term price momentum (using EMA)
    - Price volatility patterns
    - Trend strength indicators
    - Volume confirmation
    
    The evaluation returns a value between -1 and 1 where:
    - Values near -1: Strong pullback signal (potential buy)
    - Values around 0: Neutral/no clear trend
    - Values near 1: Strong momentum continuation (potential sell)
    """
    
    # Configuration parameters
    EMA_LENGTH = "ema_length"
    VOLATILITY_THRESHOLD = "volatility_threshold" 
    PULLBACK_DEPTH = "pullback_depth"
    VOLUME_MULTIPLIER = "volume_multiplier"
    
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.pertinence = 1
        self.ema_length = 20
        self.volatility_threshold = 0.5
        self.pullback_depth = 0.3
        self.volume_multiplier = 1.0
        
    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the evaluator, should define all the evaluator's user inputs
        """
        default_config = self.get_default_config()
        
        self.ema_length = self.UI.user_input(
            self.EMA_LENGTH, enums.UserInputTypes.INT, default_config["ema_length"],
            inputs, min_val=1,
            title="EMA Length: Exponential Moving Average period for trend analysis"
        )
        
        self.volatility_threshold = self.UI.user_input(
            self.VOLATILITY_THRESHOLD, enums.UserInputTypes.FLOAT, default_config["volatility_threshold"], 
            inputs, min_val=0.0,
            title="Volatility Threshold: Minimum volatility required to consider a pullback (0.0-1.0)"
        )
        
        self.pullback_depth = self.UI.user_input(
            self.PULLBACK_DEPTH, enums.UserInputTypes.FLOAT, default_config["pullback_depth"],
            inputs, min_val=0.0, max_val=1.0,
            title="Pullback Depth: Minimum pullback percentage to qualify as a valid pullback (0.0-1.0)"
        )
        
        self.volume_multiplier = self.UI.user_input(
            self.VOLUME_MULTIPLIER, enums.UserInputTypes.FLOAT, default_config["volume_multiplier"],
            inputs, min_val=0.0,
            title="Volume Multiplier: Multiplier for volume confirmation in pullback analysis"
        )

    @classmethod
    def get_default_config(cls):
        return {
            cls.EMA_LENGTH: 20,
            cls.VOLATILITY_THRESHOLD: 0.5,
            cls.PULLBACK_DEPTH: 0.3,
            cls.VOLUME_MULTIPLIER: 1.0,
        }

    async def ohlcv_callback(self, exchange: str, exchange_id: str,
                             cryptocurrency: str, symbol: str, time_frame, candle, inc_in_construction_data):
        """
        Called when new OHLCV data is available for this evaluator
        """
        # Get the complete candle data for analysis
        symbol_candles = self.get_exchange_symbol_data(exchange, exchange_id, symbol)
        
        close_candles = trading_api.get_symbol_close_candles(symbol_candles, time_frame,
                                                             include_in_construction=inc_in_construction_data)
        volume_candles = trading_api.get_symbol_volume_candles(symbol_candles, time_frame,
                                                               include_in_construction=inc_in_construction_data)
        
        await self.evaluate(cryptocurrency, symbol, time_frame, close_candles, volume_candles, candle)

    async def evaluate(self, cryptocurrency, symbol, time_frame, close_candles, volume_candles, candle):
        """
        Main evaluation method that analyzes the data and sets eval_note
        """
        # Initialize with pending value
        self.eval_note = commons_constants.START_PENDING_EVAL_NOTE
        
        if len(close_candles) >= self.ema_length + 10:  # Need enough data for analysis
            
            # Calculate EMA to identify trend direction
            ema_values = tulipy.ema(close_candles, self.ema_length)
            
            # Get the most recent close price and EMA value
            current_price = close_candles[-1]
            current_ema = ema_values[-1] if len(ema_values) > 0 else None
            
            # Calculate volatility (standard deviation of prices over a period)
            volatility_period = min(20, len(close_candles))
            price_volatility = np.std(close_candles[-volatility_period:])
            
            # Check for pullback conditions
            pullback_signal = self._analyze_pullback_conditions(
                close_candles, ema_values, current_price, current_ema, volume_candles
            )
            
            if pullback_signal is not None:
                # Set evaluation note based on the strength of the pullback signal
                self.eval_note = pullback_signal
                
        await self.evaluation_completed(cryptocurrency, symbol, time_frame,
                                        eval_time=evaluators_util.get_eval_time(full_candle=candle,
                                                                                time_frame=time_frame))

    def _analyze_pullback_conditions(self, close_candles, ema_values, current_price, current_ema, volume_candles):
        """
        Analyze price data to identify micro-trend pullbacks
        Returns a value between -1 and 1 or None if no valid signal
        """
        # Need at least some historical data for trend analysis
        if len(close_candles) < self.ema_length + 5:
            return None
            
        # Calculate recent price movement (last few candles)
        recent_prices = close_candles[-5:]
        
        # Check if we have a valid EMA value
        if current_ema is None or math.isnan(current_ema):
            return None
            
        # Determine trend direction based on EMA
        ema_trend_direction = 1 if current_price > current_ema else -1
        
        # Calculate price change percentage from EMA
        price_change_from_ema = (current_price - current_ema) / current_ema * 100
        
        # Check for pullback conditions:
        # 1. Price is below EMA (indicating potential downtrend)
        # 2. Recent price movement shows a pullback pattern
        # 3. Volatility meets minimum threshold
        # 4. Volume confirms the trend change
        
        if ema_trend_direction < 0 and abs(price_change_from_ema) > self.pullback_depth * 100:
            # Price is below EMA, indicating potential downtrend
            
            # Check recent price behavior for pullback pattern
            recent_price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            
            # If recent prices are showing upward movement while overall trend is down,
            # this could be a micro-trend pullback
            if recent_price_change > 2 and abs(recent_price_change) > self.pullback_depth * 100:
                # Volume confirmation - higher volume during potential pullbacks
                if len(volume_candles) >= 5:
                    current_volume = volume_candles[-1]
                    avg_volume = np.mean(volume_candles[-5:])
                    
                    # If volume is significantly higher than average, it confirms the signal
                    volume_confirmation = current_volume > (avg_volume * self.volume_multiplier)
                    
                    if volume_confirmation or len(volume_candles) < 5:
                        # Calculate pullback strength based on price movement and volatility
                        pullback_strength = min(1.0, abs(recent_price_change) / 100)
                        
                        # Return negative value for buy signal (pullback in downtrend)
                        return -pullback_strength * ema_trend_direction
                        
        elif ema_trend_direction > 0 and abs(price_change_from_ema) > self.pullback_depth * 100:
            # Price is above EMA, indicating potential uptrend
            
            # Check recent price behavior for pullback pattern
            recent_price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            
            # If recent prices are showing downward movement while overall trend is up,
            # this could be a micro-trend pullback
            if recent_price_change < -2 and abs(recent_price_change) > self.pullback_depth * 100:
                # Volume confirmation - higher volume during potential pullbacks
                if len(volume_candles) >= 5:
                    current_volume = volume_candles[-1]
                    avg_volume = np.mean(volume_candles[-5:])
                    
                    # If volume is significantly higher than average, it confirms the signal
                    volume_confirmation = current_volume > (avg_volume * self.volume_multiplier)
                    
                    if volume_confirmation or len(volume_candles) < 5:
                        # Calculate pullback strength based on price movement and volatility
                        pullback_strength = min(1.0, abs(recent_price_change) / 100)
                        
                        # Return positive value for sell signal (pullback in uptrend)
                        return pullback_strength * ema_trend_direction
                        
        return None

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


# Additional helper class for more advanced pullback analysis
class AdvancedMicroTrendPullbackEvaluator(evaluators.TAEvaluator):
    """
    Advanced version of micro-trend pullback evaluator with additional features.
    
    This evaluator provides enhanced analysis including:
    - Multiple time frame confirmation
    - Support/resistance level detection  
    - Enhanced volume analysis
    - Trend strength calculation
    """
    
    # Configuration parameters
    SHORT_EMA_LENGTH = "short_ema_length"
    LONG_EMA_LENGTH = "long_ema_length" 
    SUPPORT_RESISTANCE_LEVELS = "support_resistance_levels"
    VOLUME_CONFIRMATION_THRESHOLD = "volume_confirmation_threshold"
    
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.pertinence = 1
        self.short_ema_length = 10
        self.long_ema_length = 50
        self.support_resistance_levels = []
        self.volume_confirmation_threshold = 1.2
        
    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the evaluator, should define all the evaluator's user inputs
        """
        default_config = self.get_default_config()
        
        self.short_ema_length = self.UI.user_input(
            self.SHORT_EMA_LENGTH, enums.UserInputTypes.INT, default_config["short_ema_length"],
            inputs, min_val=1,
            title="Short EMA Length: Short-term Exponential Moving Average period"
        )
        
        self.long_ema_length = self.UI.user_input(
            self.LONG_EMA_LENGTH, enums.UserInputTypes.INT, default_config["long_ema_length"],
            inputs, min_val=1,
            title="Long EMA Length: Long-term Exponential Moving Average period"
        )
        
        # Support/resistance levels would be defined in the config
        self.support_resistance_levels = self.UI.user_input(
            self.SUPPORT_RESISTANCE_LEVELS, enums.UserInputTypes.OBJECT_ARRAY,
            [], inputs, other_schema_values={"minItems": 0, "uniqueItems": True},
            item_title="Support/Resistance Level",
            title="Support and resistance levels to consider in analysis"
        )
        
        self.volume_confirmation_threshold = self.UI.user_input(
            self.VOLUME_CONFIRMATION_THRESHOLD, enums.UserInputTypes.FLOAT, 
            default_config["volume_confirmation_threshold"],
            inputs, min_val=0.0,
            title="Volume Confirmation Threshold: Minimum volume multiplier for confirmation"
        )

    @classmethod
    def get_default_config(cls):
        return {
            cls.SHORT_EMA_LENGTH: 10,
            cls.LONG_EMA_LENGTH: 50,
            cls.SUPPORT_RESISTANCE_LEVELS: [],
            cls.VOLUME_CONFIRMATION_THRESHOLD: 1.2,
        }

    async def ohlcv_callback(self, exchange: str, exchange_id: str,
                             cryptocurrency: str, symbol: str, time_frame, candle, inc_in_construction_data):
        """
        Called when new OHLCV data is available for this evaluator
        """
        # Get the complete candle data for analysis
        symbol_candles = self.get_exchange_symbol_data(exchange, exchange_id, symbol)
        
        close_candles = trading_api.get_symbol_close_candles(symbol_candles, time_frame,
                                                             include_in_construction=inc_in_construction_data)
        volume_candles = trading_api.get_symbol_volume_candles(symbol_candles, time_frame,
                                                               include_in_construction=inc_in_construction_data)
        
        await self.evaluate(cryptocurrency, symbol, time_frame, close_candles, volume_candles, candle)

    async def evaluate(self, cryptocurrency, symbol, time_frame, close_candles, volume_candles, candle):
        """
        Main evaluation method that analyzes the data and sets eval_note
        """
        # Initialize with pending value
        self.eval_note = commons_constants.START_PENDING_EVAL_NOTE
        
        if len(close_candles) >= max(self.short_ema_length, self.long_ema_length) + 10:
            # Calculate EMAs for trend analysis
            short_ema = tulipy.ema(close_candles, self.short_ema_length)
            long_ema = tulipy.ema(close_candles, self.long_ema_length)
            
            # Get the most recent close price and EMA values
            current_price = close_candles[-1]
            current_short_ema = short_ema[-1] if len(short_ema) > 0 else None
            current_long_ema = long_ema[-1] if len(long_ema) > 0 else None
            
            # Analyze pullback conditions with multiple time frame confirmation
            pullback_signal = self._analyze_advanced_pullback_conditions(
                close_candles, short_ema, long_ema, current_price, 
                current_short_ema, current_long_ema, volume_candles
            )
            
            if pullback_signal is not None:
                # Set evaluation note based on the strength of the pullback signal
                self.eval_note = pullback_signal
                
        await self.evaluation_completed(cryptocurrency, symbol, time_frame,
                                        eval_time=evaluators_util.get_eval_time(full_candle=candle,
                                                                                time_frame=time_frame))

    def _analyze_advanced_pullback_conditions(self, close_candles, short_ema, long_ema, current_price, 
                                              current_short_ema, current_long_ema, volume_candles):
        """
        Analyze price data with advanced techniques for micro-trend pullbacks
        Returns a value between -1 and 1 or None if no valid signal
        """
        # Need at least some historical data for trend analysis
        if len(close_candles) < max(self.short_ema_length, self.long_ema_length) + 5:
            return None
            
        # Check EMA crossovers for trend confirmation
        ema_trend_direction = 0
        
        if current_short_ema is not None and current_long_ema is not None:
            if current_short_ema > current_long_ema:
                ema_trend_direction = 1  # Uptrend
            elif current_short_ema < current_long_ema:
                ema_trend_direction = -1  # Downtrend
                
        # Calculate recent price movement (last few candles)
        if len(close_candles) >= 5:
            recent_prices = close_candles[-5:]
            recent_price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            
            # Check for pullback pattern with volume confirmation
            if len(volume_candles) >= 5:
                current_volume = volume_candles[-1]
                avg_volume = np.mean(volume_candles[-5:])
                
                # Volume confirmation threshold
                volume_confirmation = current_volume > (avg_volume * self.volume_confirmation_threshold)
                
                # Check for pullback conditions based on trend direction
                if ema_trend_direction < 0 and recent_price_change > 2:
                    # Pullback in downtrend - potential buy signal
                    return -min(1.0, abs(recent_price_change) / 50)
                    
                elif ema_trend_direction > 0 and recent_price_change < -2:
                    # Pullback in uptrend - potential sell signal  
                    return min(1.0, abs(recent_price_change) / 50)
                
        return None

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