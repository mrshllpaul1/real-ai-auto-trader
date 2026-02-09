# AI Pipeline Enhancement Plan

## 1) Current pipelines & bottlenecks
- **Prediction signals**: Aggregates order book, on-chain, social, transformer, RL, cross-asset, and advanced TA. Bottlenecks: sequential calls, inconsistent timeouts, missing fallbacks for some components, and limited visibility into per-component latency.
- **Optimization/adaptivity**: Adaptive params derived from regime detection; no explicit guardrails for exposure drift and no cached reuse of stable params when upstream signals are slow.
- **Learning/evaluation**: Limited automatic replay/backtest coverage for new signal blends; lacks regression suite for hit-rate/PNL drift.
- **Auto-trader (spot/weekly)**: Budget isolation present; real-trade safety relies on env flag. Bottlenecks: ticker fetch latency, lack of pXX latency SLOs, and no structured safety metrics (blocked-by-AI, budget-deny).

## 2) Enhancement goals & metrics
- **Signal quality**: Improve precision/recall of buy/sell calls. Track: hit rate (profitable trades / total), precision per signal class, win-rate %, average PNL per trade, drawdown per regime.
- **Latency**: p50/p95/p99 for `/api/spot/ai-recommendations`, prediction fan-out, and order placement paths. Target <2s p95 for recommendations; <3s for spot trade decision (paper).
- **Safety**: Zero unintended real trades without flag; rate of AI-blocked trades vs executed; stop-loss/take-profit trigger counts; budget-deny rate.
- **Adaptivity**: Regime detection freshness (<10 min), adaptive param cache reuse hit-rate, and exposure drift vs target bands.

## 3) Proposed improvements (architecture/data/features)
- **Prediction pipeline**
  - Add per-component timeouts and partial-result merging; cache last-good component outputs with timestamps.
  - Batch transformer/RL calls; add lightweight heuristic fallback when ML models unavailable.
  - Record per-component latency/health in the response for observability.
- **Optimization/adaptivity**
  - Cache latest adaptive params with TTL; reuse on component timeouts to keep responses fast.
  - Enforce exposure/position-size clamps in one place (max_exposure, max_position_pct).
- **Learning/evaluation**
  - Add offline replay harness for recent ticks to score composite signals (precision/recall, PNL delta) before enabling changes.
  - Add backtest regression suite for top symbols with fixed seeds to prevent quality regressions.
- **Auto-trader safety/perf**
  - Keep real-trade guard (env flag) and log safety metrics (AI blocks, budget-deny).
  - Prefer cached prices when Kraken is slow; define per-endpoint p95 targets and alert when exceeded.

## 4) Validation & test approach
- **API smoke**: Ensure `/api/spot/ai-recommendations` returns composite block, component latencies, and optimization metadata.
- **Latency checks**: Add lightweight timing assertions in performance tests (p95 thresholds) once instrumentation is in place.
- **Safety tests**: Verify env-gated real trading stays blocked by default; budget/AI block paths return structured errors.
- **Offline evaluation**: Run replay/backtest suites for hit-rate/win-rate and PNL before promoting new models or weight changes.
