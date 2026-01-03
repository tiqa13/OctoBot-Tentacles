import decimal
import math
import octobot_commons.constants as commons_constants
import octobot_evaluators.evaluators as evaluators
import octobot_trading.enums as trading_enums
import octobot_trading.modes as trading_modes


class MakerFirstRangeMRStrategy(evaluators.StrategyEvaluator):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        
        # Strategy parameters
        self.range_regime_evaluator = None
        self.entry_evaluator = None
        
        # Trading parameters
        self.tp_percent_range = (0.3, 0.5)  # TP range from entry: 0.3% to 0.5%
        self.sl_percent_range = (-0.3, -0.2)  # SL range from entry: -0.2% to -0.3%
        self.cooldown_candles = 3  # Cooldown period after exit
        self.max_positions = 1  # Only one position at a time
        
    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        """
        :return: True if the strategy is not symbol dependant else False
        """
        return False

    @classmethod
    def get_is_time_frame_wildcard(cls) -> bool:
        """
        :return: True if the strategy is not time_frame dependant else False
        """
        return False
        
    async def matrix_callback(self, evaluator_name, indicator_name, matrix, cryptocurrency, symbol, time_frame):
        # Get evaluation from both evaluators
        range_regime_eval = None
        entry_eval = None
        
        # Find the range regime evaluator
        if self.range_regime_evaluator is not None:
            range_regime_eval = await self.get_eval_from_matrix(
                matrix, 
                cryptocurrency, 
                symbol, 
                time_frame,
                self.range_regime_evaluator
            )
        
        # Find the entry evaluator  
        if self.entry_evaluator is not None:
            entry_eval = await self.get_eval_from_matrix(
                matrix, 
                cryptocurrency, 
                symbol, 
                time_frame,
                self.entry_evaluator
            )
            
        # Combine evaluations according to strategy logic
        final_note = commons_constants.START_PENDING_EVAL_NOTE
        
        if range_regime_eval is not None and entry_eval is not None:
            # Only trade when regime evaluator indicates range (value == 1)
            if range_regime_eval == 1:  # Range regime enabled
                # Use the entry evaluator's signal for direction
                final_note = entry_eval
                
        # Set the evaluation note
        self.eval_note = final_note
        
        # Notify that evaluation is complete
        await self.evaluation_completed(cryptocurrency, symbol, time_frame)

    async def get_eval_from_matrix(self, matrix, cryptocurrency, symbol, time_frame, evaluator_name):
        """
        Helper method to extract evaluation from the matrix for a specific evaluator.
        """
        try:
            # Get the node from the matrix
            evaluator_node = matrix.get_tentacle_node(
                exchange_name=self.exchange_manager.exchange_name,
                tentacle_type=evaluators.evaluators_enums.EvaluatorMatrixTypes.TA.value,
                cryptocurrency=cryptocurrency,
                symbol=symbol,
                time_frame=time_frame,
                tentacle_name=evaluator_name
            )
            
            if evaluator_node is not None:
                return evaluator_node.get_eval_note()
        except Exception as e:
            self.logger.error(f"Error getting evaluation from matrix for {evaluator_name}: {e}")
        
        return None

    def set_default_evaluators(self, tentacles_setup_config):
        """
        Set default evaluators to use with this strategy.
        This method is called by the trading mode when setting up the strategy.
        """
        # These will be set by the trading mode during initialization
        pass
        
    async def create_state(self, cryptocurrency: str, symbol: str, time_frame):
        """
        Called after evaluation completion to determine state and potentially trigger orders.
        This is where we would implement our specific logic for when to trade based on combined evaluations.
        """
        # The strategy will be handled by the trading mode which will use self.eval_note
        pass

    def get_trading_mode_config(self):
        """
        Return configuration parameters that can be used in the trading mode.
        """
        return {
            "tp_percent_range": self.tp_percent_range,
            "sl_percent_range": self.sl_percent_range,
            "cooldown_candles": self.cooldown_candles
        }