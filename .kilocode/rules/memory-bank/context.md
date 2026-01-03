# Trailing Stop Trading Mode for OctoBot

## Description
A modular, stateless, deterministic OctoBot tentacle that manages open positions using adaptive trailing stops to improve profitability. Features include ATR-based trailing, profit-tier locking, partial take-profits, break-even adjustments, time-based exits, and evaluator signals (trend, volatility, momentum).

## Goals
- Implement adaptive ATR trailing stop
- Integrate R-multiple profit-tier locking
- Support partial take-profit + break-even logic
- Add time-based exit rules
- Consume evaluator inputs: trend, volatility, momentum
- Log metrics: entry/exit, MAE/MFE, R captured, trail distance
- Maintain modular, stateless design

## Constraints
- Code must be deterministic and stateless
- Use OctoBot API standards
- Tasks must be executed incrementally
- Keep each step minimal to conserve tokens

## Next Steps
1. Initialize project files (create context.md, tasks.md, tasks_micro.md)
2. Implement core ATR trailing engine
3. Implement profit-tier logic
4. Implement partial TP & break-even
5. Add time-based exit rules
6. Integrate evaluators
7. Implement logging and metrics
8. Write unit and integration tests
