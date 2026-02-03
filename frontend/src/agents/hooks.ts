// Agent 관련 React 훅

import { useState, useEffect, useCallback } from 'react';
import { agentClient, AgentRequest, AgentResponse } from './agentClient';

/**
 * Agent 실행 훅
 */
export const useAgent = <T = any>() => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(async (request: AgentRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await agentClient.executeAgent<T>(request);
      
      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError(response.error || 'Agent execution failed');
      }
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { execute, loading, error, data, reset };
};

/**
 * Agent 상태 모니터링 훅
 */
export const useAgentStatus = (agentType?: string, pollInterval = 5000) => {
  const [status, setStatus] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const response = agentType
          ? await agentClient.getAgentStatus(agentType)
          : await agentClient.getAllAgentsStatus();
        
        setStatus(response);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    
    if (pollInterval > 0) {
      intervalId = setInterval(fetchStatus, pollInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [agentType, pollInterval]);

  return { status, loading, error };
};

/**
 * Agent 헬스체크 훅
 */
export const useAgentHealth = (checkInterval = 30000) => {
  const [isHealthy, setIsHealthy] = useState(true);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const checkHealth = async () => {
      const healthy = await agentClient.healthCheck();
      setIsHealthy(healthy);
      setLastCheck(new Date());
    };

    checkHealth();
    
    if (checkInterval > 0) {
      intervalId = setInterval(checkHealth, checkInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [checkInterval]);

  return { isHealthy, lastCheck };
};

/**
 * Data Ingestion Agent 훅
 */
export const useDataIngestion = () => {
  const { execute, loading, error, data } = useAgent();

  const ingestData = useCallback(async (provider?: string) => {
    return await execute({
      agentType: 'data_ingestion',
      action: 'crawl',
      params: { provider },
    });
  }, [execute]);

  const getIngestionStatus = useCallback(async () => {
    return await execute({
      agentType: 'data_ingestion',
      action: 'status',
    });
  }, [execute]);

  return {
    ingestData,
    getIngestionStatus,
    loading,
    error,
    data,
  };
};

/**
 * Monitoring Agent 훅
 */
export const useMonitoring = () => {
  const { execute, loading, error, data } = useAgent();

  const getMetrics = useCallback(async (timeRange?: string) => {
    return await execute({
      agentType: 'monitoring',
      action: 'get_metrics',
      params: { timeRange },
    });
  }, [execute]);

  const getAlerts = useCallback(async () => {
    return await execute({
      agentType: 'monitoring',
      action: 'get_alerts',
    });
  }, [execute]);

  return {
    getMetrics,
    getAlerts,
    loading,
    error,
    data,
  };
};
