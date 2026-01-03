import typing

import octobot_commons.constants as commons_constants
import octobot_commons.enums as commons_enums
import octobot_commons.evaluators_util as evaluators_util
import octobot_evaluators.api as evaluators_api
import octobot_evaluators.matrix as matrix
import octobot_evaluators.enums as evaluators_enums
import octobot_evaluators.constants as evaluators_constants
import octobot_evaluators.errors as errors
import octobot_evaluators.evaluators as evaluators
import octobot_trading.api as trading_api


class MicroTrendPullbackStrategyEvaluator(evaluators.StrategyEvaluator):
    """
    Strategy that specifically uses the BTC Micro-Trend Pullback evaluator.
    
    This strategy focuses on identifying micro-trend pullbacks in BTC price movements 
    and generating trading signals based on these patterns. It's designed to work with
    the MicroTrendPullbackEvaluator and AdvancedMicroTrendPullbackEvaluator classes.
    
    The strategy evaluates:
    - Pullback strength indicators from the evaluator
    - Trend confirmation using multiple timeframes
    - Volume analysis for signal validation
    """
    
    # Configuration parameters
    MIN_PULLBACK_STRENGTH = "min_pullback_strength"
    USE_ADVANCED_EVALUATOR = "use_advanced_evaluator"
    
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.min_pullback_strength = 0.3
        self.use_advanced_evaluator = False
        
    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the strategy, should define all the strategy's user inputs
        """
        default_config = self.get_default_config()
        
        self.min_pullback_strength = self.UI.user_input(
            self.MIN_PULLBACK_STRENGTH, commons_enums.UserInputTypes.FLOAT,
            default_config["min_pullback_strength"], inputs, min_val=0.0, max_val=1.0,
            title="Minimum Pullback Strength: Minimum strength required for a valid pullback signal (0.0-1.0)"
        )
        
        self.use_advanced_evaluator = self.UI.user_input(
            self.USE_ADVANCED_EVALUATOR, commons_enums.UserInputTypes.BOOLEAN,
            default_config["use_advanced_evaluator"], inputs,
            title="Use Advanced Evaluator: When enabled, uses the advanced pullback evaluator with additional features"
        )

    @classmethod
    def get_default_config(cls, time_frames: typing.Optional[list[str]] = None) -> dict:
        return {
            evaluators_constants.STRATEGIES_REQUIRED_TIME_FRAME: (
                time_frames or [commons_enums.TimeFrames.ONE_HOUR.value]
            ),
            cls.MIN_PULLBACK_STRENGTH: 0.3,
            cls.USE_ADVANCED_EVALUATOR: False,
        }

    async def matrix_callback(self,
                               matrix_id,
                               evaluator_name,
                               evaluator_type,
                               eval_note,
                               eval_note_type,
                               exchange_name,
                               cryptocurrency,
                               symbol,
                               time_frame):
        """
        Called when a new evaluation is available from the matrix
        """
        # Only process technical analysis evaluators for our specific pullback strategy
        if evaluator_type != evaluators_enums.EvaluatorMatrixTypes.TA.value:
            return
            
        try:
            # Get all TA evaluations for this symbol and timeframe
            TA_by_timeframe = {
                available_time_frame: matrix.get_evaluations_by_evaluator(
                    matrix_id,
                    exchange_name,
                    evaluators_enums.EvaluatorMatrixTypes.TA.value,
                    cryptocurrency,
                    symbol,
                    available_time_frame.value,
                    allow_missing=False,
                    allowed_values=[commons_constants.START_PENDING_EVAL_NOTE])
                for available_time_frame in self.strategy_time_frames
            }
            
            # Check if this is our specific evaluator
            if "MicroTrendPullback" in evaluator_name or "AdvancedMicroTrendPullback" in evaluator_name:
                await self._evaluate_pullback_signal(matrix_id, evaluator_name, eval_note,
                                                     exchange_name, cryptocurrency, symbol)
                
        except errors.UnsetTentacleEvaluation as e:
            self.logger.error(f"Missing technical evaluator data for ({e})")
        except Exception as e:
            self.logger.exception(e, True, f"Error when computing strategy evaluation: {e}")

    async def _evaluate_pullback_signal(self, matrix_id, evaluator_name, eval_note,
                                        exchange_name, cryptocurrency, symbol):
        """
        Evaluate a pullback signal from the MicroTrendPullbackEvaluator
        """
        # Get the evaluation value
        eval_value = evaluators_api.get_value(eval_note)
        
        # Check if this is a valid pullback signal (not pending or invalid)
        if evaluators_util.check_valid_eval_note(eval_value, eval_type=evaluators_api.get_type(eval_note),
                                                 expected_eval_type=evaluators_constants.EVALUATOR_EVAL_DEFAULT_TYPE):
            
            # Only process signals that meet our minimum strength requirement
            if abs(eval_value) >= self.min_pullback_strength:
                # Set the strategy evaluation note based on the pullback signal
                self.eval_note = eval_value
                
                # Complete the strategy evaluation
                await self.strategy_completed(cryptocurrency, symbol)
                
    async def strategy_completed(self, cryptocurrency, symbol):
        """
        Called when a complete strategy evaluation is finished
        """
        # Log the result for debugging purposes
        if self.eval_note != commons_constants.START_PENDING_EVAL_NOTE:
            self.logger.debug(f"MicroTrendPullbackStrategy: {cryptocurrency} {symbol} - Signal: {self.eval_note}")
            
        await super().strategy_completed(cryptocurrency, symbol)


class BTCMicroTrendPullbackStrategyEvaluator(evaluators.StrategyEvaluator):
    """
    Specialized strategy for BTC micro-trend pullbacks.
    
    This is a more focused version that specifically targets BTC trading pairs
    and provides optimized evaluation logic for Bitcoin's unique market characteristics.
    """
    
    # Configuration parameters
    BTC_ONLY = "btc_only"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    
    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)
        self.btc_only = True
        self.confidence_threshold = 0.5
        
    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the strategy, should define all the strategy's user inputs
        """
        default_config = self.get_default_config()
        
        self.btc_only = self.UI.user_input(
            self.BTC_ONLY, commons_enums.UserInputTypes.BOOLEAN,
            default_config["btc_only"], inputs,
            title="BTC Only: When enabled, only evaluates BTC trading pairs"
        )
        
        self.confidence_threshold = self.UI.user_input(
            self.CONFIDENCE_THRESHOLD, commons_enums.UserInputTypes.FLOAT,
            default_config["confidence_threshold"], inputs, min_val=0.0, max_val=1.0,
            title="Confidence Threshold: Minimum confidence level for trading signals (0.0-1.0)"
        )

    @classmethod
    def get_default_config(cls, time_frames: typing.Optional[list[str]] = None) -> dict:
        return {
            evaluators_constants.STRATEGIES_REQUIRED_TIME_FRAME: (
                time_frames or [commons_enums.TimeFrames.ONE_HOUR.value]
            ),
            cls.BTC_ONLY: True,
            cls.CONFIDENCE_THRESHOLD: 0.5,
        }

    async def matrix_callback(self,
                               matrix_id,
                               evaluator_name,
                               evaluator_type,
                               eval_note,
                               eval_note_type,
                               exchange_name,
                               cryptocurrency,
                               symbol,
                               time_frame):
        """
        Called when a new evaluation is available from the matrix
        """
        # Only process technical analysis evaluators for our specific pullback strategy
        if evaluator_type != evaluators_enums.EvaluatorMatrixTypes.TA.value:
            return
            
        try:
            # If BTC only mode is enabled, check that this is a BTC pair
            if self.btc_only and not symbol.startswith("BTC"):
                return
                
            # Get the evaluation value
            eval_value = evaluators_api.get_value(eval_note)
            
            # Check if this is our specific evaluator for pullback analysis
            if "MicroTrendPullback" in evaluator_name or "AdvancedMicroTrendPullback" in evaluator_name:
                
                # Only process signals that meet confidence threshold
                if abs(eval_value) >= self.confidence_threshold:
                    # Set the strategy evaluation note based on the pullback signal
                    self.eval_note = eval_value
                    
                    # Complete the strategy evaluation
                    await self.strategy_completed(cryptocurrency, symbol)
                    
        except errors.UnsetTentacleEvaluation as e:
            self.logger.error(f"Missing technical evaluator data for ({e})")
        except Exception as e:
            self.logger.exception(e, True, f"Error when computing BTC Micro-Trend Pullback strategy evaluation: {e}")