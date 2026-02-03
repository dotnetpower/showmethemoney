// 애플리케이션 설정

interface AppConfig {
  apiBaseUrl: string;
  apiTimeout: number;
  enableMockData: boolean;
  enableDebugMode: boolean;
  cacheTTL: number;
  retryAttempts: number;
  retryDelay: number;
}

const config: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
  enableMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
  enableDebugMode: import.meta.env.MODE === 'development',
  cacheTTL: 300000, // 5 minutes
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

export default config;

// 환경별 설정
export const isDevelopment = import.meta.env.MODE === 'development';
export const isProduction = import.meta.env.MODE === 'production';
export const isTest = import.meta.env.MODE === 'test';

// Feature Flags
export const FEATURES = {
  ENABLE_PORTFOLIO: true,
  ENABLE_TOTAL_RETURN: true,
  ENABLE_DIVIDEND_SIMULATOR: true,
  ENABLE_ADVANCED_CHARTS: true,
  ENABLE_EXPORT: true,
  ENABLE_NOTIFICATIONS: false, // 향후 구현
  ENABLE_AGENT_INTEGRATION: false, // Phase 1에서 구현
} as const;
