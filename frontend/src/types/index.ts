// 공통 타입 정의
export interface ETF {
  ticker: string;
  name: string;
  provider: string;
  price?: number;
  dividendYield?: number;
  expenseRatio?: number;
  aum?: number;
  inceptionDate?: string;
  category?: string;
  description?: string;
}

export interface DividendInfo {
  ticker: string;
  name: string;
  dividendYield: number;
  paymentFrequency: string;
  exDividendDate?: string;
  paymentDate?: string;
  amount?: number;
}

export interface TotalReturnETF extends ETF {
  totalReturn1Year?: number;
  totalReturn3Year?: number;
  totalReturn5Year?: number;
  totalReturn10Year?: number;
  sinceInception?: number;
}

export interface Portfolio {
  id: string;
  name: string;
  holdings: Holding[];
  totalValue: number;
  createdAt: string;
  updatedAt: string;
}

export interface Holding {
  ticker: string;
  shares: number;
  averagePrice: number;
  currentPrice?: number;
  totalValue?: number;
  gainLoss?: number;
  gainLossPercent?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationParams {
  page: number;
  perPage: number;
  total?: number;
}

export interface FilterParams {
  provider?: string;
  category?: string;
  minDividendYield?: number;
  maxExpenseRatio?: number;
  minAum?: number;
  search?: string;
}

export interface SortParams {
  field: string;
  order: 'asc' | 'desc';
}
