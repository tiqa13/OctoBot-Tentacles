# Trailing Stop Trading Mode

The Trailing Stop Trading Mode is an advanced trading mode that manages open positions using adaptive trailing stops to improve profitability. It features ATR-based trailing, profit-tier locking, partial take-profits, break-even adjustments, time-based exits, and evaluator signal integration.

## Key Features

### ATR-Based Trailing Stop
The mode uses Average True Range (ATR) to dynamically adjust stop-loss levels based on market volatility. This ensures that positions are protected during volatile periods while allowing room for normal price fluctuations during calmer periods.

### Profit-Tier Locking
As positions move in your favor, the mode progressively locks in profits at configurable R-multiples. This ensures that gains are preserved while allowing the remaining position to continue capturing potential upside.

### Partial Take-Profit Orders
The mode can create multiple partial take-profit orders at different price levels, allowing you to capture profits at various targets while maintaining a portion of the position for continued potential gains.

### Break-Even Adjustments
When positions reach a configurable profit threshold, the stop-loss can be adjusted to break-even or a slightly positive level, protecting your capital while maintaining upside potential.

### Time-Based Exit Rules
Positions can be automatically closed after a configurable number of bars, preventing positions from remaining open indefinitely and helping manage risk.

### Evaluator Signal Integration
The mode integrates with trend, volatility, and momentum evaluators to adjust trailing behavior based on market conditions, optimizing performance across different market environments.

## Configuration

### ATR Settings
- **ATR Period**: The period used for calculating the Average True Range (default: 14)
- **ATR Multiplier**: The multiplier applied to the ATR for stop distance (default: 2)

### Profit Tiers
- **R-Multiples**: Configurable profit tiers at which stop-losses are progressively locked
- **Lock Percentages**: The percentage of position to lock at each profit tier

### Partial Take-Profit
- **Percentages**: The percentage of position to close at each take-profit level
- **R-Multiples**: The R-multiple targets for each partial take-profit

### Risk Management
- **Break-Even R-Multiple**: The profit level at which to adjust stop-loss to break-even
- **Max Trade Duration**: Maximum number of bars a position can remain open

### Evaluator Integration
- **Trend Filter**: Enable/disable integration with trend evaluators
- **Volatility Filter**: Enable/disable integration with volatility evaluators
- **Momentum Filter**: Enable/disable integration with momentum evaluators

## Usage

To use the Trailing Stop Trading Mode, simply select it in your OctoBot configuration and configure the parameters according to your risk tolerance and trading preferences. The mode works best with strategies that provide clear entry signals and benefit from adaptive trailing stop management.