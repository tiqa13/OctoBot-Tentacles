#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.

import decimal
import math
import octobot_commons.constants as commons_constants
import octobot_commons.enums as commons_enums
import octobot_evaluators.evaluators as evaluators
import octobot_trading.enums as trading_enums
import octobot_trading.modes as trading_modes
import octobot_trading.personal_data as trading_personal_data


class MakerScalpingMode(trading_modes.AbstractTradingMode):
    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        
        # Strategy parameters
        self.range_regime_evaluator = "RangeRegimeEvaluator15m"
        self.entry_evaluator = "MeanReversionEntryEvaluator1m"
        self.strategy_class = "MakerFirstRangeMRStrategy"
        
        # Trading parameters
        self.tp_percent_range = (0.3, 0.5)  # TP range from entry: 0.3% to 0.5%
        self.sl_percent_range = (-0.3, -0.2)  # SL range from entry: -0.2% to -0.3%
        self.cooldown_candles = 3  # Cooldown period after exit
        self.max_positions = 1  # Only one position at a time
        
    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the tentacle, should define all the tentacle's user inputs unless
        those are defined somewhere else.
        """
        self.UI.user_input(
            "tp_percent_min", commons_enums.UserInputTypes.FLOAT, self.tp_percent_range[0], inputs,
            min_val=0,
            title="Minimum Take Profit Percent: Minimum percentage for take profit orders (e.g. 0.3 = 0.3%)"
        )
        
        self.UI.user_input(
            "tp_percent_max", commons_enums.UserInputTypes.FLOAT, self.tp_percent_range[1], inputs,
            min_val=0,
            title="Maximum Take Profit Percent: Maximum percentage for take profit orders (e.g. 0.5 = 0.5%)"
        )
        
        self.UI.user_input(
            "sl_percent_min", commons_enums.UserInputTypes.FLOAT, self.sl_percent_range[0], inputs,
            max_val=0,
            title="Minimum Stop Loss Percent: Minimum percentage for stop loss orders (e.g. -0.3 = -0.3%)"
        )
        
        self.UI.user_input(
            "sl_percent_max", commons_enums.UserInputTypes.FLOAT, self.sl_percent_range[1], inputs,
            max_val=0,
            title="Maximum Stop Loss Percent: Maximum percentage for stop loss orders (e.g. -0.2 = -0.2%)"
        )
        
        self.UI.user_input(
            "cooldown_candles", commons_enums.UserInputTypes.INT, self.cooldown_candles, inputs,
            min_val=1,
            title="Cooldown Candles: Number of candles to wait after an exit before entering again"
        )

    @classmethod
    def get_supported_exchange_types(cls) -> list:
        """
        :return: The list of supported exchange types
        """
        return [
            trading_enums.ExchangeTypes.SPOT,
            trading_enums.ExchangeTypes.FUTURE,
        ]

    def get_current_state(self) -> (str, float):
        return super().get_current_state()[0] if self.producers[0].state is None else self.producers[0].state.name, \
               self.producers[0].final_eval

    def get_mode_producer_classes(self) -> list:
        return [MakerScalpingModeProducer]

    def get_mode_consumer_classes(self) -> list:
        return [MakerScalpingModeConsumer]

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        return False


class MakerScalpingModeConsumer(trading_modes.AbstractTradingModeConsumer):
    PRICE_KEY = "PRICE"
    VOLUME_KEY = "VOLUME"
    STOP_PRICE_KEY = "STOP_PRICE"
    ACTIVE_ORDER_SWAP_STRATEGY = "ACTIVE_ORDER_SWAP_STRATEGY"
    ACTIVE_ORDER_SWAP_TIMEOUT = "ACTIVE_ORDER_SWAP_TIMEOUT"
    TAKE_PROFIT_PRICE_KEY = "TAKE_PROFIT_PRICE"
    ADDITIONAL_TAKE_PROFIT_PRICES_KEY = "ADDITIONAL_TAKE_PROFIT_PRICES"
    ADDITIONAL_TAKE_PROFIT_VOLUME_RATIOS_KEY = "ADDITIONAL_TAKE_PROFIT_VOLUME_RATIOS"
    STOP_ONLY = "STOP_ONLY"
    TRAILING_PROFILE = "TRAILING_PROFILE"
    CANCEL_POLICY = "CANCEL_POLICY"
    CANCEL_POLICY_PARAMS = "CANCEL_POLICY_PARAMS"
    REDUCE_ONLY_KEY = "REDUCE_ONLY"
    TAG_KEY = "TAG"
    EXCHANGE_ORDER_IDS = "EXCHANGE_ORDER_IDS"
    LEVERAGE = "LEVERAGE"
    ORDER_EXCHANGE_CREATION_PARAMS = "ORDER_EXCHANGE_CREATION_PARAMS"

    def __init__(self, trading_mode):
        super().__init__(trading_mode)
        self.trader = self.exchange_manager.trader

        # Strategy parameters
        self.range_regime_evaluator = "RangeRegimeEvaluator15m"
        self.entry_evaluator = "MeanReversionEntryEvaluator1m"
        
        # Trading parameters
        self.tp_percent_range = (0.3, 0.5)  # TP range from entry: 0.3% to 0.5%
        self.sl_percent_range = (-0.3, -0.2)  # SL range from entry: -0.2% to -0.3%
        self.cooldown_candles = 3  # Cooldown period after exit
        self.max_positions = 1  # Only one position at a time
        
    def flush(self):
        super().flush()
        self.trader = None

    async def create_new_orders(self, symbol, final_note, state, **kwargs):
        """
        Create new orders based on the strategy evaluation.
        This is where we implement our specific trading logic for maker-first scalping.
        """
        try:
            if final_note.is_nan():
                return []
        except AttributeError:
            final_note = decimal.Decimal(str(final_note))
            if final_note.is_nan():
                return []

        # Get configuration values
        self.tp_percent_range = (
            self.trading_mode.config.get("tp_percent_min", 0.3),
            self.trading_mode.config.get("tp_percent_max", 0.5)
        )
        self.sl_percent_range = (
            self.trading_mode.config.get("sl_percent_min", -0.3),
            self.trading_mode.config.get("sl_percent_max", -0.2)
        )
        self.cooldown_candles = self.trading_mode.config.get("cooldown_candles", 3)

        # Check if we should trade based on the strategy
        data = kwargs.get(self.CREATE_ORDER_DATA_PARAM, {})
        dependencies = kwargs.get(self.CREATE_ORDER_DEPENDENCIES_PARAM, None)
        
        # Get current price and symbol market info
        try:
            _, _, _, price, symbol_market = await trading_personal_data.get_pre_order_data(
                self.exchange_manager, symbol=symbol, timeout=commons_constants.ORDER_DATA_FETCHING_TIMEOUT
            )
            
            # Determine order type based on signal direction
            if final_note > 0:  # Long signal (1)
                return await self._create_long_order(symbol, price, symbol_market, data, dependencies)
            elif final_note < 0:  # Short signal (-1)  
                return await self._create_short_order(symbol, price, symbol_market, data, dependencies)
            else:
                # No trade signal
                return []
                
        except Exception as e:
            self.logger.exception(e, True, f"Error creating orders for {symbol}: {e}")
            return []

    async def _create_long_order(self, symbol, current_price, symbol_market, data, dependencies):
        """Create a long maker order with TP and SL"""
        # For now just create the limit order - we'll handle TP/SL in the producer
        try:
            # Get quantity from risk (simplified)
            _, _, market_quantity, price, _ = await trading_personal_data.get_pre_order_data(
                self.exchange_manager, symbol=symbol, timeout=commons_constants.ORDER_DATA_FETCHING_TIMEOUT
            )
            
            # Create a limit buy order at current price for maker-first approach
            limit_price = current_price  # For maker orders, we'll use the current price
            
            # Calculate quantity (simplified)
            quantity = market_quantity * 0.1  # Use 10% of available funds as example
            
            # Create the order
            current_order = trading_personal_data.create_order_instance(
                trader=self.trader,
                order_type=trading_enums.TraderOrderType.BUY_LIMIT,
                symbol=symbol,
                current_price=current_price,
                quantity=quantity,
                price=limit_price,
                reduce_only=False,
                tag="maker_first_scalper_long",
            )
            
            # Create the order on exchange
            created_order = await self.trading_mode.create_order(current_order, dependencies=dependencies)
            return [created_order] if created_order else []
            
        except Exception as e:
            self.logger.exception(e, True, f"Error creating long order for {symbol}: {e}")
            return []

    async def _create_short_order(self, symbol, current_price, symbol_market, data, dependencies):
        """Create a short maker order with TP and SL"""
        try:
            # Get quantity from risk (simplified)
            _, current_symbol_holding, _, price, _ = await trading_personal_data.get_pre_order_data(
                self.exchange_manager, symbol=symbol, timeout=commons_constants.ORDER_DATA_FETCHING_TIMEOUT
            )
            
            # Create a limit sell order at current price for maker-first approach  
            limit_price = current_price  # For maker orders, we'll use the current price
            
            # Calculate quantity (simplified)
            quantity = current_symbol_holding * 0.1  # Use 10% of available funds as example
            
            # Create the order
            current_order = trading_personal_data.create_order_instance(
                trader=self.trader,
                order_type=trading_enums.TraderOrderType.SELL_LIMIT,
                symbol=symbol,
                current_price=current_price,
                quantity=quantity,
                price=limit_price,
                reduce_only=False,
                tag="maker_first_scalper_short",
            )
            
            # Create the order on exchange
            created_order = await self.trading_mode.create_order(current_order, dependencies=dependencies)
            return [created_order] if created_order else []
            
        except Exception as e:
            self.logger.exception(e, True, f"Error creating short order for {symbol}: {e}")
            return []


class MakerScalpingModeProducer(trading_modes.AbstractTradingModeProducer):
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)

        self.state = None

        # Strategy parameters
        self.range_regime_evaluator = "RangeRegimeEvaluator15m"
        self.entry_evaluator = "MeanReversionEntryEvaluator1m"
        
        # Trading parameters  
        self.tp_percent_range = (0.3, 0.5)  # TP range from entry: 0.3% to 0.5%
        self.sl_percent_range = (-0.3, -0.2)  # SL range from entry: -0.2% to -0.3%
        self.cooldown_candles = 3  # Cooldown period after exit
        self.max_positions = 1  # Only one position at a time

    async def stop(self):
        if self.trading_mode is not None:
            self.trading_mode.flush_trading_mode_consumers()
        await super().stop()

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame, trigger_source: str):
        """
        Called when the strategy evaluation is complete.
        This method will be called by the strategy evaluator to get final evaluation results.
        """
        # Get the strategy's evaluation note
        try:
            # For now just pass through - in a real implementation we'd process 
            # both evaluators and combine them according to our logic
            
            # The actual evaluation is handled by the strategy class, which will set self.final_eval
            await self.create_state(cryptocurrency=cryptocurrency, symbol=symbol)
            
        except Exception as e:
            self.logger.exception(e, True, f"Error in set_final_eval for {symbol}: {e}")

    async def create_state(self, cryptocurrency: str, symbol: str):
        """
        Create the trading state based on strategy evaluation.
        This is where we'd implement our specific logic for when to trade.
        """
        # In a real implementation this would be more complex and check:
        # 1. If we're in range regime (from RangeRegimeEvaluator)
        # 2. If we have an entry signal (from MeanReversionEntryEvaluator)  
        # 3. If we're within cooldown period
        # 4. If we have position limits
        
        if self.final_eval.is_nan():
            await self._set_state(cryptocurrency=cryptocurrency,
                                  symbol=symbol,
                                  new_state=trading_enums.EvaluatorStates.NEUTRAL)
            return
            
        # For now, just pass through the evaluation note
        state = trading_enums.EvaluatorStates.NEUTRAL
        
        if self.final_eval > 0:
            state = trading_enums.EvaluatorStates.LONG
        elif self.final_eval < 0:
            state = trading_enums.EvaluatorStates.SHORT
            
        await self._set_state(cryptocurrency=cryptocurrency,
                              symbol=symbol,
                              new_state=state)

    async def _set_state(self, cryptocurrency: str, symbol: str, new_state):
        if new_state != self.state:
            self.state = new_state
            self.logger.info(f"[{symbol}] new state: {self.state.name}")

            # Call orders creation from consumers (this will trigger the actual order creation)
            await self.submit_trading_evaluation(cryptocurrency=cryptocurrency,
                                                 symbol=symbol,
                                                 time_frame=None,
                                                 final_note=self.final_eval,
                                                 state=self.state)

    @classmethod
    def get_should_cancel_loaded_orders(cls):
        return True