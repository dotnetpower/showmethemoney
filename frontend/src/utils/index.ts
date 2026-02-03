// 유틸리티 함수

/**
 * 숫자를 통화 형식으로 포맷팅
 */
export const formatCurrency = (value: number, currency = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * 숫자를 퍼센트 형식으로 포맷팅
 */
export const formatPercent = (value: number, decimals = 2): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * 큰 숫자를 축약 형식으로 포맷팅 (1.5M, 2.3B 등)
 */
export const formatCompactNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

/**
 * 날짜를 포맷팅
 */
export const formatDate = (date: string | Date, format = 'short'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (format === 'short') {
    return dateObj.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } else if (format === 'long') {
    return dateObj.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  } else if (format === 'time') {
    return dateObj.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
    });
  }
  
  return dateObj.toLocaleDateString('en-US');
};

/**
 * 디바운스 함수
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * 쓰로틀 함수
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * 로컬 스토리지에서 값 가져오기
 */
export const getFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error reading from localStorage: ${error}`);
    return defaultValue;
  }
};

/**
 * 로컬 스토리지에 값 저장
 */
export const setToLocalStorage = <T>(key: string, value: T): void => {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing to localStorage: ${error}`);
  }
};

/**
 * 로컬 스토리지에서 값 제거
 */
export const removeFromLocalStorage = (key: string): void => {
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage: ${error}`);
  }
};

/**
 * 배열을 특정 크기의 청크로 분할
 */
export const chunkArray = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

/**
 * 객체의 빈 값 제거
 */
export const removeEmptyValues = <T extends Record<string, any>>(obj: T): Partial<T> => {
  return Object.entries(obj).reduce((acc, [key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      acc[key as keyof T] = value;
    }
    return acc;
  }, {} as Partial<T>);
};

/**
 * 딥 카피
 */
export const deepCopy = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * 클래스명 결합
 */
export const classNames = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

/**
 * 랜덤 ID 생성
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 9);
};

/**
 * Sleep 함수 (비동기)
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 에러 메시지 추출
 */
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
};
