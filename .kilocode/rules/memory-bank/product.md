# Product

## What this repository is
`OctoBot-Tentacles` is a repository of tentacles (plug-in modules) for the [OctoBot](https://github.com/Drakkar-Software/OctoBot) trading framework. It contains the **default** set of evaluators, strategies, trading modes, services, and related utilities used by OctoBot.

This repository is packaged as a tentacles package (`metadata.yaml`) and is typically installed/loaded by OctoBot’s tentacles manager.

## Who it is for
- OctoBot users who want ready-to-use, maintained tentacles (technical analysis, strategies, trading modes, services).
- Developers building or customizing tentacles following OctoBot’s tentacle API conventions.

## What problems it solves
- Provides a curated baseline of trading logic (TA evaluators, strategies, trading modes) so users don’t start from scratch.
- Supplies service integrations (web interface, telegram bots/notifiers, webhooks, feeds) needed to run and operate OctoBot.
- Includes backtesting tooling tentacles (collectors/importers) for data collection and simulation workflows.
- Provides sample *profiles* that bundle configuration + tentacle activation sets.

## How it is used (high-level)
- OctoBot loads tentacles from this repository into their respective module type folders (Evaluator, Trading, Services, etc.). See [`README.md`](../../README.md:1).
- Each tentacle package folder typically contains:
  - `metadata.json` describing the tentacle classes exported by that package.
  - optional `config/*.json` providing default configuration.
  - optional `resources/*.md` providing user-facing documentation.
  - optional `tests/` with pytest-based tests.
- End users enable/disable tentacles via a tentacles setup config (example: [`profiles/daily_trading/tentacles_config.json`](../../profiles/daily_trading/tentacles_config.json:1)) and can use ready-made profiles (example: [`profiles/daily_trading/profile.json`](../../profiles/daily_trading/profile.json:1)).
