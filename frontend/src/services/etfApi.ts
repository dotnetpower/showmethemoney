/**
 * ETF API 서비스
 */

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
  distribution_yield: string | null;
  distribution_frequency: string;
  product_page_url: string;
  detail_page_url: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * 모든 ETF 목록을 통합하여 가져옵니다.
 */
export async function getAllETFs(): Promise<ETF[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/etf/all`);
    if (!response.ok) {
      throw new Error(`Failed to fetch ETFs: ${response.statusText}`);
    }
    return await response.json();
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
