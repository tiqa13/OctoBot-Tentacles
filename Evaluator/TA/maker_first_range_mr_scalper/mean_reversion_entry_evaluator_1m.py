import math
import tulipy
import octobot_commons.constants as commons_constants
import octobot_evaluators.evaluators as evaluators
import octobot_evaluators.util as evaluators_util
import octobot_trading.api as trading_api


class MeanReversionEntryEvaluator1m(evaluators.TAEvaluator):
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.pertinence = 1
        # Bollinger Bands parameters
        self.bb_period = 20
        self.bb_std_dev = 2
        # RSI parameters
        self.rsi_period = 14
        # RSI thresholds for mean reversion signals
        self.rsi_overbought = 70
        self.rsi_oversold = 30

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the evaluator, should define all the evaluator's user inputs
        """
        self.bb_period = self.UI.user_input(
            "bb_period", 
            enums.UserInputTypes.INT, 
            self.bb_period,
            inputs,
            min_val=1,
            title="BB Period: Bollinger Bands period length"
        )
        
        self.bb_std_dev = self.UI.user_input(
            "bb_std_dev", 
            enums.UserInputTypes.FLOAT, 
            self.bb_std_dev,
            inputs,
            min_val=0.1,
            title="BB Standard Deviation: Number of standard deviations for Bollinger Bands"
        )
        
        self.rsi_period = self.UI.user_input(
            "rsi_period", 
            enums.UserInputTypes.INT, 
            self.rsi_period,
            inputs,
            min_val=1,
            title="RSI Period: RSI period length"
        )
        
        self.rsi_overbought = self.UI.user_input(
            "rsi_overbought", 
            enums.UserInputTypes.INT, 
            self.rsi_overbought,
            inputs,
            min_val=50,
            max_val=100,
            title="RSI Overbought: RSI value above which price is considered overbought"
        )
        
        self.rsi_oversold = self.UI.user_input(
            "rsi_oversold", 
            enums.UserInputTypes.INT, 
            self.rsi_oversold,
            inputs,
            min_val=0,
            max_val=50,
            title="RSI Oversold: RSI value below which price is considered oversold"
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
        min_data_length = max(self.bb_period + 2, self.rsi_period + 1)
        
        if len(close_candles) >= min_data_length:
            # Calculate Bollinger Bands
            bb_lower, bb_middle, bb_upper = tulipy.bbands(close_candles, self.bb_period, self.bb_std_dev)
            
            # Calculate RSI
            rsi_values = tulipy.rsi(close_candles, self.rsi_period)
            
            # Remove NaN values from the end of arrays (tulipy may return some NaNs at beginning)
            bb_clean = [val for val in bb_lower if not math.isnan(val)]
            rsi_clean = [val for val in rsi_values if not math.isnan(val)]
            
            # Check if we have enough clean data
            if len(bb_clean) >= 2 and len(rsi_clean) >= 2:
                # Get the latest values
                current_close = close_candles[-1]
                previous_close = close_candles[-2] 
                current_bb_lower = bb_clean[-1]
                current_bb_upper = bb_clean[-2] if len(bb_clean) > 1 else bb_clean[-1]
                current_rsi = rsi_clean[-1]
                previous_rsi = rsi_clean[-2]
                
                # Check for long signal: price below lower BB and RSI turning up
                if (current_close <= current_bb_lower and 
                    current_rsi < self.rsi_oversold and 
                    current_rsi > previous_rsi):
                    self.eval_note = 1  # Long signal
                    
                # Check for short signal: price above upper BB and RSI turning down  
                elif (current_close >= current_bb_upper and 
                      current_rsi > self.rsi_overbought and 
                      current_rsi < previous_rsi):
                    self.eval_note = -1  # Short signal
                    
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