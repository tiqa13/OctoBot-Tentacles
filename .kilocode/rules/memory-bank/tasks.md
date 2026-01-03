# tasks.md

## Task 1: Initialize project files
- Create `context.md` with project description, goals, and constraints
- Create empty `tasks.md` file
- Mark as "done"

## Task 2: Define project tasks
- Break the Trailing Stop Mode project into smallest possible tasks
- Include subtasks for:
  - ATR-based trailing engine
  - R-multiple profit-tier logic
  - Partial TP + break-even
  - Time-based exits
  - Evaluator integration
  - Logging and metrics
- Mark as "in progress"

## Task 3: Implement core ATR trailing engine
- Create file: `trailing_stop_mode.py`
- Implement basic ATR-based stop calculation for long/short
- Keep modular and stateless
- Mark as "pending"

## Task 4: Implement profit-tier logic
- Add configurable R-multiples
- Lock stops progressively as profit tiers are reached
- Mark as "pending"

## Task 5: Implement partial take-profit + break-even
- Support configurable TP percentages
- Adjust stops after partial TP
- Mark as "pending"

## Task 6: Add time-based exit rules
- Max bars in trade
- Exit or tighten stop if exceeded
- Mark as "pending"

## Task 7: Integrate evaluators
- Accept trend, volatility, and momentum inputs
- Adjust trailing behavior accordingly
- Mark as "pending"

## Task 8: Logging and metrics
- Log entry/exit prices
- Track MAE, MFE, R captured, exit reason, trail distance
- Mark as "pending"

## Task 9: Testing
- Unit tests for each component
- Ensure stateless and deterministic behavior
- Mark as "pending"
