# Architecture

## High-level structure
This repository is a *tentacles package* (see [`metadata.yaml`](../../metadata.yaml:1)). It is meant to be loaded by OctoBot’s tentacles manager and provides multiple tentacle types.

At a high level, tentacles are organized by **module type** directories:
- [`Evaluator/`](../../Evaluator:1) — evaluators for market/TA/social signals and utilities.
- [`Trading/`](../../Trading:1) — trading modes and exchange-related trading components.
- [`Services/`](../../Services:1) — interfaces (web UI, telegram bot interface), notifiers, service bases and feeds.
- [`Backtesting/`](../../Backtesting:1) — backtesting data collectors/importers/converters.
- [`Meta/`](../../Meta:1) — DSL operators and keywords used by OctoBot scripting.
- [`Automation/`](../../Automation:1) — automation actions/conditions/trigger events.
- [`profiles/`](../../profiles:1) — ready-made OctoBot profiles combining bot config + tentacle activation.

## Tentacle package layout (common pattern)
Most tentacle packages follow this pattern:
- A folder per package (example: [`Evaluator/TA/momentum_evaluator/`](../../Evaluator/TA/momentum_evaluator:1)).
- `metadata.json` listing:
  - exported tentacle class names (`"tentacles"`)
  - package version
  - `origin_package` tag (example: `OctoBot-Default-Tentacles`)
  - optional `tentacles-requirements` (dependency on other tentacle packages)
  See [`Evaluator/TA/momentum_evaluator/metadata.json`](../../Evaluator/TA/momentum_evaluator/metadata.json:1) and [`Trading/Mode/daily_trading_mode/metadata.json`](../../Trading/Mode/daily_trading_mode/metadata.json:1).
- Optional `config/*.json` providing defaults and/or required tentacles for that module (example: [`Trading/Mode/daily_trading_mode/config/DailyTradingMode.json`](../../Trading/Mode/daily_trading_mode/config/DailyTradingMode.json:1)).
- Optional `resources/*.md` documentation rendered by the web interface (example: [`Trading/Mode/daily_trading_mode/resources/DailyTradingMode.md`](../../Trading/Mode/daily_trading_mode/resources/DailyTradingMode.md:1)).
- Optional `tests/` containing `pytest` tests (often `pytest-asyncio`).

## Evaluators
### Types and locations
Evaluators are grouped in:
- [`Evaluator/TA/`](../../Evaluator/TA:1): technical analysis evaluators (often using `tulipy`/`numpy`).
- [`Evaluator/Strategies/`](../../Evaluator/Strategies:1): strategy evaluators that aggregate other evaluators.
- [`Evaluator/Social/`](../../Evaluator/Social:1): social/news/signal evaluators.
- [`Evaluator/RealTime/`](../../Evaluator/RealTime:1): real-time market evaluators.
- [`Evaluator/Util/`](../../Evaluator/Util:1): shared analysis/utilities.

### Typical execution model
A TA evaluator (example: [`RSIMomentumEvaluator`](../../Evaluator/TA/momentum_evaluator/momentum.py:30)) typically:
- Defines runtime configuration via `init_user_inputs()`.
- Receives market data via async callbacks like `ohlcv_callback()`.
- Computes an `eval_note` and finalizes via `evaluation_completed()`.

A strategy evaluator (example: [`SimpleStrategyEvaluator`](../../Evaluator/Strategies/mixed_strategies_evaluator/mixed_strategies.py:34)) listens to matrix callbacks and aggregates multiple evaluator types (TA/real-time/social) into a final strategy note.

## Trading modes
Trading modes are implemented under [`Trading/Mode/`](../../Trading/Mode:1). Example: [`DailyTradingMode`](../../Trading/Mode/daily_trading_mode/daily_trading.py:47).

Common characteristics:
- A trading mode declares supported exchange types and exposes producer/consumer classes.
- Producers compute a **state** (e.g., LONG/SHORT/NEUTRAL) from strategy evaluation(s) and publish it.
- Consumers convert state changes + risk settings into concrete order creation/cancellation logic.

Trading mode documentation and defaults are typically in `resources/` and `config/` within the same package.

## Services
Services provide user interfaces and notifications.

Key areas:
- Web interface: [`Services/Interfaces/web_interface/`](../../Services/Interfaces/web_interface:1), implemented as a Flask application (example class: [`WebInterface`](../../Services/Interfaces/web_interface/web.py:47)).
- Telegram bot interface: [`Services/Interfaces/telegram_bot_interface/`](../../Services/Interfaces/telegram_bot_interface:1) (example class: [`TelegramBotInterface`](../../Services/Interfaces/telegram_bot_interface/telegram_bot.py:34)).
- Notifiers, service bases, and feeds under [`Services/Notifiers/`](../../Services/Notifiers:1), [`Services/Services_bases/`](../../Services/Services_bases:1), and [`Services/Services_feeds/`](../../Services/Services_feeds:1).

## Backtesting
Backtesting-related tentacles live under [`Backtesting/`](../../Backtesting:1) and include exchange collectors/importers.

Example: [`ExchangeLiveDataCollector`](../../Backtesting/collectors/exchanges/exchange_live_collector/live_collector.py:31) subscribes to trading channels and persists live data for later use.

## Meta / DSL
The Meta layer extends OctoBot’s scripting DSL via operators.

Example: [`TAOperator`](../../Meta/DSL_operators/ta_operators/ta_operator.py:23) declares the `ta` operator library, and exchange operators use `exchange` (see [`ExchangeOperator`](../../Meta/DSL_operators/exchange_operators/exchange_operator.py:27)).

## Profiles
Profiles under [`profiles/`](../../profiles:1) are ready-made configurations:
- `profile.json` contains bot configuration + profile metadata (example: [`profiles/daily_trading/profile.json`](../../profiles/daily_trading/profile.json:1)).
- `tentacles_config.json` contains tentacle activation mapping by category (example: [`profiles/daily_trading/tentacles_config.json`](../../profiles/daily_trading/tentacles_config.json:1)).
- `specific_config/` may contain per-profile overrides for specific tentacles.
