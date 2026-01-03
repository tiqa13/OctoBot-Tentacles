import tulipy

import octobot_commons.constants as commons_constants
import octobot_commons.enums as commons_enums
import octobot_evaluators.evaluators as evaluators
import octobot_evaluators.util as evaluators_util
import octobot_trading.api as trading_api


class EMAgptEvaluator(evaluators.TAEvaluator):

    FAST_PERIOD = "fast_period"
    SLOW_PERIOD = "slow_period"
    PRICE_THRESHOLD_PERCENT = "price_threshold_percent"
    REVERSE_SIGNAL = "reverse_signal"
    MOMENTUM_LOOKBACK = "momentum_lookback"
    MIN_SLOPE = "min_slope"
    PERSISTENCE_CANDLES = "persistence_candles"

    def __init__(self, tentacles_setup_config):
        super().__init__(tentacles_setup_config)

        # ===== OPTIMIZED DEFAULTS (BTC 1m, MAKER, FEES AWARE) =====
        self.fast_period = 21
        self.slow_period = 100
        self.price_threshold_percent = 0.25  # >= fees
        self.reverse_signal = False
        self.momentum_lookback = 3
        self.min_slope = 0.00025
        self.persistence_candles = 2

        self.signal_history = {}

    def init_user_inputs(self, inputs: dict) -> None:
        cfg = self.get_default_config()

        self.fast_period = self.UI.user_input(
            self.FAST_PERIOD,
            commons_enums.UserInputTypes.INT,
            cfg[self.FAST_PERIOD],
            inputs,
            min_val=1,
            title="Fast EMA period"
        )

        self.slow_period = self.UI.user_input(
            self.SLOW_PERIOD,
            commons_enums.UserInputTypes.INT,
            cfg[self.SLOW_PERIOD],
            inputs,
            min_val=1,
            title="Slow EMA period"
        )

        self.price_threshold_percent = self.UI.user_input(
            self.PRICE_THRESHOLD_PERCENT,
            commons_enums.UserInputTypes.FLOAT,
            cfg[self.PRICE_THRESHOLD_PERCENT],
            inputs,
            min_val=0.1,
            title="Minimum price distance from EMA (%)"
        )

        self.reverse_signal = self.UI.user_input(
            self.REVERSE_SIGNAL,
            commons_enums.UserInputTypes.BOOLEAN,
            cfg[self.REVERSE_SIGNAL],
            inputs,
            title="Reverse signal"
        )

        self.momentum_lookback = self.UI.user_input(
            self.MOMENTUM_LOOKBACK,
            commons_enums.UserInputTypes.INT,
            cfg[self.MOMENTUM_LOOKBACK],
            inputs,
            min_val=1,
            title="Momentum lookback candles"
        )

        self.min_slope = self.UI.user_input(
            self.MIN_SLOPE,
            commons_enums.UserInputTypes.FLOAT,
            cfg[self.MIN_SLOPE],
            inputs,
            min_val=0.0001,
            title="Minimum EMA slope (normalized)"
        )

        self.persistence_candles = self.UI.user_input(
            self.PERSISTENCE_CANDLES,
            commons_enums.UserInputTypes.INT,
            cfg[self.PERSISTENCE_CANDLES],
            inputs,
            min_val=1,
            title="Signal persistence candles"
        )

    @classmethod
    def get_default_config(cls) -> dict:
        return {
            cls.FAST_PERIOD: 21,
            cls.SLOW_PERIOD: 100,
            cls.PRICE_THRESHOLD_PERCENT: 0.25,
            cls.REVERSE_SIGNAL: False,
            cls.MOMENTUM_LOOKBACK: 3,
            cls.MIN_SLOPE: 0.00025,
            cls.PERSISTENCE_CANDLES: 2
        }

    async def ohlcv_callback(
        self,
        exchange: str,
        exchange_id: str,
        cryptocurrency: str,
        symbol: str,
        time_frame,
        candle,
        inc_in_construction_data
    ):

        if symbol not in self.signal_history:
            self.signal_history[symbol] = {}
        if time_frame not in self.signal_history[symbol]:
            self.signal_history[symbol][time_frame] = []

        depth = max(self.fast_period, self.slow_period, self.momentum_lookback) + 50

        closes = trading_api.get_symbol_close_candles(
            self.get_exchange_symbol_data(exchange, exchange_id, symbol),
            time_frame,
            depth,
            include_in_construction=inc_in_construction_data
        )

        highs = trading_api.get_symbol_high_candles(
            self.get_exchange_symbol_data(exchange, exchange_id, symbol),
            time_frame,
            depth,
            include_in_construction=inc_in_construction_data
        )

        lows = trading_api.get_symbol_low_candles(
            self.get_exchange_symbol_data(exchange, exchange_id, symbol),
            time_frame,
            depth,
            include_in_construction=inc_in_construction_data
        )

        await self.evaluate(
            cryptocurrency,
            symbol,
            time_frame,
            closes,
            highs,
            lows,
            candle
        )

    async def evaluate(
        self,
        cryptocurrency,
        symbol,
        time_frame,
        closes,
        highs,
        lows,
        candle
    ):

        self.eval_note = commons_constants.START_PENDING_EVAL_NOTE

        if len(closes) < self.slow_period + 2:
            return

        # ===== EMA CALCULATION =====
        ema_fast = tulipy.ema(closes, self.fast_period)
        ema_slow = tulipy.ema(closes, self.slow_period)

        ema_slow_last = ema_slow[-1]
        price = closes[-1]

        # ===== NORMALIZED SLOPE FILTER =====
        slope = (ema_slow[-1] - ema_slow[-2]) / ema_slow_last
        if abs(slope) < self.min_slope:
            return

        # ===== ATR-BASED DISTANCE =====
        atr = tulipy.atr(highs, lows, closes, 14)[-1]
        dynamic_threshold = max(
            self.price_threshold_percent / 100,
            atr / price
        )

        # ===== NO-TRADE ZONE (FEE PROTECTION) =====
        ema_distance = abs(price - ema_slow_last) / ema_slow_last
        if ema_distance < dynamic_threshold * 0.8:
            return

        # ===== MOMENTUM (NORMALIZED) =====
        momentum = (
            price - closes[-self.momentum_lookback]
        ) / closes[-self.momentum_lookback]

        signal = 0

        if (
            ema_fast[-1] > ema_slow_last and
            price > ema_slow_last * (1 + dynamic_threshold) and
            momentum > 0
        ):
            signal = 1

        elif (
            ema_fast[-1] < ema_slow_last and
            price < ema_slow_last * (1 - dynamic_threshold) and
            momentum < 0
        ):
            signal = -1

        if self.reverse_signal:
            signal = -signal

        # ===== SIGNAL PERSISTENCE =====
        history = self.signal_history[symbol][time_frame]
        history.append(signal)

        if len(history) > self.persistence_candles:
            history.pop(0)

        if signal != 0 and history.count(signal) < self.persistence_candles:
            signal = 0

        self.eval_note = signal

        await self.evaluation_completed(
            cryptocurrency,
            symbol,
            time_frame,
            eval_time=evaluators_util.get_eval_time(
                full_candle=candle,
                time_frame=time_frame
            )
        )
