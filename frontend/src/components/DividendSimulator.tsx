import { useState, useCallback } from "react";
import {
  simulateDividend,
  DividendSimulationResult,
} from "../services/etfApi";

const DividendSimulator = () => {
  const [ticker, setTicker] = useState("");
  const [investmentAmount, setInvestmentAmount] = useState("");
  const [holdingPeriod, setHoldingPeriod] = useState("12");
  const [result, setResult] = useState<DividendSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = useCallback(async () => {
    if (!ticker || !investmentAmount) {
      setError("티커와 투자 금액을 입력해주세요.");
      return;
    }

    const amount = parseFloat(investmentAmount);
    if (isNaN(amount) || amount <= 0) {
      setError("올바른 투자 금액을 입력해주세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const simulationResult = await simulateDividend({
        ticker: ticker.toUpperCase(),
        investment_amount: amount,
        holding_period_months: parseInt(holdingPeriod),
      });
      setResult(simulationResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "시뮬레이션에 실패했습니다.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [ticker, investmentAmount, holdingPeriod]);

  const formatCurrency = (value: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(parseFloat(value));
  };

  return (
    <article className="card simulator-card">
      <h2>💰 배당금 시뮬레이터</h2>
      <p className="simulator-description">
        ETF에 투자했을 때 예상 배당금을 계산해보세요.
      </p>

      <div className="simulator-form">
        <div className="form-group">
          <label htmlFor="ticker">ETF 티커</label>
          <input
            id="ticker"
            type="text"
            placeholder="예: SCHD, SPY, JEPI"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="simulator-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="investment">투자 금액 (USD)</label>
          <input
            id="investment"
            type="number"
            placeholder="10000"
            value={investmentAmount}
            onChange={(e) => setInvestmentAmount(e.target.value)}
            className="simulator-input"
            min="1"
            step="100"
          />
        </div>

        <div className="form-group">
          <label htmlFor="period">보유 기간</label>
          <select
            id="period"
            value={holdingPeriod}
            onChange={(e) => setHoldingPeriod(e.target.value)}
            className="simulator-select"
          >
            <option value="3">3개월</option>
            <option value="6">6개월</option>
            <option value="12">1년</option>
            <option value="24">2년</option>
            <option value="36">3년</option>
            <option value="60">5년</option>
          </select>
        </div>

        <button
          onClick={handleSimulate}
          disabled={loading}
          className="simulator-button"
        >
          {loading ? "계산 중..." : "배당금 계산"}
        </button>
      </div>

      {error && <div className="simulator-error">{error}</div>}

      {result && (
        <div className="simulator-result">
          <h3>{result.fund_name}</h3>
          <div className="result-grid">
            <div className="result-item">
              <span className="result-label">현재 가격</span>
              <span className="result-value">{formatCurrency(result.current_price)}</span>
            </div>
            <div className="result-item">
              <span className="result-label">구매 가능 주수</span>
              <span className="result-value">{parseFloat(result.shares_purchased).toFixed(2)} 주</span>
            </div>
            <div className="result-item">
              <span className="result-label">배당 수익률</span>
              <span className="result-value highlight">{parseFloat(result.distribution_yield).toFixed(2)}%</span>
            </div>
            <div className="result-item">
              <span className="result-label">월간 예상 배당금</span>
              <span className="result-value">{formatCurrency(result.monthly_dividend_estimate)}</span>
            </div>
            <div className="result-item">
              <span className="result-label">연간 예상 배당금</span>
              <span className="result-value">{formatCurrency(result.annual_dividend_estimate)}</span>
            </div>
            <div className="result-item featured">
              <span className="result-label">{result.holding_period_months}개월 총 예상 배당금</span>
              <span className="result-value featured-value">{formatCurrency(result.total_dividend_estimate)}</span>
            </div>
          </div>
          <p className="result-disclaimer">
            * 예상 배당금은 현재 배당 수익률을 기준으로 계산되며, 실제 배당금은 변동될 수 있습니다.
          </p>
        </div>
      )}
    </article>
  );
};

export default DividendSimulator;
