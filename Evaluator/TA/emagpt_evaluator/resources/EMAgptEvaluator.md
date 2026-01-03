# EMAgpt Evaluator

The EMAgpt evaluator is a technical analysis tool that uses Exponential Moving Averages (EMA) with additional filters to generate trading signals.

## How it works

The evaluator uses two EMAs (fast and slow) along with several filters to generate buy/sell signals:

1. **EMA Crossover**: Fast EMA crossing above or below the slow EMA
2. **Slope Filter**: Ensures the slow EMA has sufficient slope to confirm trend direction
3. **Dynamic Threshold**: Uses ATR-based dynamic threshold to filter out weak signals
4. **Momentum Filter**: Rate of Change filter to confirm momentum
5. **Signal Persistence**: Requires multiple consecutive signals to reduce false positives

## Configuration

- **Fast EMA period**: The period for the fast EMA (default: 21)
- **Slow EMA period**: The period for the slow EMA (default: 100)
- **Price threshold percent**: Dynamic threshold based on ATR (default: 0.2%)
- **Reverse signal**: Option to reverse the signal direction (default: false)
- **Momentum lookback**: Lookback period for momentum calculation (default: 3)
- **Minimum slope**: Minimum slope required for slow EMA (default: 0.00005)
- **Persistence candles**: Number of consecutive signals required (default: 2)