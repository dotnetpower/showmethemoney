// 애플리케이션 상수

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const PROVIDERS = [
  'iShares',
  'Vanguard',
  'SPDR',
  'Invesco',
  'GlobalX',
  'FirstTrust',
  'Direxion',
  'Franklin Templeton',
  'JPMorgan',
  'Goldman Sachs',
  'Pacer Advisors',
  'Roundhill',
  'Dimensional Fund Advisors',
  'PIMCO',
  'Alpha Architect',
  'Fidelity',
  'GraniteShares',
  'VanEck',
  'WisdomTree',
  'Yieldmax',
] as const;

export const CATEGORIES = [
  'Equity',
  'Fixed Income',
  'Commodity',
  'Currency',
  'Alternative',
  'Multi-Asset',
  'Real Estate',
] as const;

export const PAYMENT_FREQUENCIES = [
  'Monthly',
  'Quarterly',
  'Semi-Annual',
  'Annual',
] as const;

export const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
] as const;

export const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

export const CHART_COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  danger: '#ef4444',
  warning: '#f59e0b',
  info: '#06b6d4',
  light: '#f3f4f6',
  dark: '#1f2937',
} as const;

export const ROUTES = {
  HOME: '/',
  ETF_LIST: '/etf-list',
  DIVIDEND_SCHEDULE: '/dividend-schedule',
  DIVIDEND_SIMULATOR: '/dividend-simulator',
  TOTAL_RETURN: '/total-return',
  PORTFOLIO: '/portfolio',
  SETTINGS: '/settings',
  ABOUT: '/about',
} as const;

export const LOCAL_STORAGE_KEYS = {
  THEME: 'smtm_theme',
  FAVORITES: 'smtm_favorites',
  PORTFOLIO: 'smtm_portfolio',
  SETTINGS: 'smtm_settings',
} as const;

export const DEFAULT_PAGINATION = {
  page: 1,
  perPage: 50,
} as const;

export const DEBOUNCE_DELAY = 300; // ms
export const CACHE_TTL = 300000; // 5 minutes in ms
