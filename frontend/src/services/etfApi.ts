/**
 * ETF API 서비스
 */

export interface InvestorRating {
  source: string;
  rating: string | null;
  score: string | null;
  analyst_rating: string | null;
  url: string | null;
  last_updated: string | null;
}

export interface DividendHistory {
  ex_date: string;
  pay_date: string | null;
  amount: string;
  currency: string;
}

export interface ETF {
  ticker: string;
  fund_name: string;
  isin: string;
  cusip: string;
  inception_date: string | null;
  nav_amount: string;
  nav_as_of: string;
  expense_ratio: string;
  ytd_return: string | null;
  one_year_return: string | null;
  three_year_return: string | null;
  five_year_return: string | null;
  ten_year_return: string | null;
  since_inception_return: string | null;
  asset_class: string;
  region: string;
  market_type: string;
  sector: string | null;
  theme: string | null;
  distribution_yield: string | null;
  distribution_frequency: string;
  ratings: InvestorRating[] | null;
  dividend_history: DividendHistory[] | null;
  data_source: string | null;
  last_updated: string | null;
  product_page_url: string;
  detail_page_url: string;
}

export interface DividendSimulationRequest {
  ticker: string;
  investment_amount: number;
  holding_period_months: number;
}

export interface DividendSimulationResult {
  ticker: string;
  fund_name: string;
  investment_amount: string;
  shares_purchased: string;
  current_price: string;
  distribution_yield: string;
  annual_dividend_estimate: string;
  monthly_dividend_estimate: string;
  holding_period_months: number;
  total_dividend_estimate: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * 모든 ETF 목록을 통합하여 가져옵니다.
 */
export async function getAllETFs(): Promise<ETF[]> {
  try {
    console.log(`API URL: ${API_BASE_URL}/api/v1/etf/all`);
    const response = await fetch(`${API_BASE_URL}/api/v1/etf/all`);
    if (!response.ok) {
      throw new Error(`Failed to fetch ETFs: ${response.statusText}`);
    }
    const data = await response.json();

    // 응답 데이터 검증
    if (!Array.isArray(data)) {
      console.error("API response is not an array:", data);
      throw new Error("Invalid API response: expected an array");
    }

    console.log(`API returned ${data.length} ETFs`);
    return data;
  } catch (error) {
    console.error("Error fetching ETFs:", error);
    throw error;
  }
}

/**
 * 특정 운용사의 ETF 목록을 가져옵니다.
 */
export async function getETFsByProvider(provider: string): Promise<ETF[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/etf/list/${provider}`);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch ETFs for ${provider}: ${response.statusText}`
      );
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching ETFs for ${provider}:`, error);
    throw error;
  }
}

/**
 * 배당금 시뮬레이션을 수행합니다.
 */
export async function simulateDividend(
  request: DividendSimulationRequest
): Promise<DividendSimulationResult> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/etf/simulate-dividend`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to simulate dividend: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error simulating dividend:", error);
    throw error;
  }
}
