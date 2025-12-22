# Tech

## Primary language
- Python (project is a tentacles package consumed by the OctoBot runtime).

## Key runtime dependencies (as seen in tentacle imports)
This repository’s tentacles integrate with the OctoBot ecosystem packages, for example:
- `octobot_commons` (constants, enums, logging, utilities)
- `octobot_evaluators` (base evaluator classes, matrix/event system)
- `octobot_trading` (exchange managers, trading modes, personal data)
- `octobot_services` (interfaces/notifiers, service abstractions)
- `octobot_tentacles_manager` (loading/configuration APIs)

## Common third-party dependencies (used by tentacles)
- Numeric/TA:
  - `numpy`
  - `tulipy` (technical indicators) — used by TA evaluators (example: [`Evaluator/TA/momentum_evaluator/momentum.py`](../../Evaluator/TA/momentum_evaluator/momentum.py:16))
- Web interface:
  - `flask`, `flask_cors`, `flask_socketio`
  - `flask_compress`, `flask_caching`
  - async mode shown as `gevent` in SocketIO setup (example: [`Services/Interfaces/web_interface/web.py`](../../Services/Interfaces/web_interface/web.py:214))
- Telegram interface:
  - `python-telegram-bot` (`telegram.ext`, `telegram.constants`) (example: [`Services/Interfaces/telegram_bot_interface/telegram_bot.py`](../../Services/Interfaces/telegram_bot_interface/telegram_bot.py:20))

## Testing
- `pytest` with `pytest.mark.asyncio` is used broadly for async components (examples: [`Evaluator/Social/signal_evaluator/tests/test_telegram_channel_signal_evaluator.py`](../../Evaluator/Social/signal_evaluator/tests/test_telegram_channel_signal_evaluator.py:17), [`Services/Interfaces/telegram_bot_interface/tests/test_bot_interface.py`](../../Services/Interfaces/telegram_bot_interface/tests/test_bot_interface.py:16)).

## Repository/package metadata
- Root package metadata is defined in [`metadata.yaml`](../../metadata.yaml:1).
- Each tentacle subpackage exports its tentacle classes via a local `metadata.json` (example: [`Evaluator/TA/momentum_evaluator/metadata.json`](../../Evaluator/TA/momentum_evaluator/metadata.json:1)).

## Configuration assets
- User-facing default OctoBot config example: [`octobot_config.json`](../../octobot_config.json:1).
- Profiles bundle bot config + activation mapping under [`profiles/`](../../profiles:1).

## Notable implementation patterns
- Tentacles rely on OctoBot callback-driven execution (e.g., `ohlcv_callback`, `matrix_callback`).
- Many modules include `resources/*.md` which are rendered/linked from the web interface.
