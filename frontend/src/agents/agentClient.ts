// Agent Framework 통합 레이어
// Microsoft Agent Framework와 React 프론트엔드를 연결하는 클라이언트

import axios, { AxiosInstance } from 'axios';
import config from '../config';

export interface AgentRequest {
  agentType: 'data_ingestion' | 'data_processing' | 'monitoring' | 'api' | 'storage';
  action: string;
  params?: Record<string, any>;
}

export interface AgentResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  executionTime?: number;
  agentInfo?: {
    name: string;
    version: string;
    status: string;
  };
}

class AgentClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${config.apiBaseUrl}/api/v1/agents`,
      timeout: config.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        // 디버그 모드에서 요청 로깅
        if (config.enableDebugMode) {
          console.log('[Agent Request]', config);
        }
        return config;
      },
      (error) => {
        console.error('[Agent Request Error]', error);
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => {
        if (config.enableDebugMode) {
          console.log('[Agent Response]', response);
        }
        return response;
      },
      (error) => {
        console.error('[Agent Response Error]', error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Agent에게 요청 전송
   */
  async executeAgent<T>(request: AgentRequest): Promise<AgentResponse<T>> {
    try {
      const response = await this.client.post<AgentResponse<T>>('/execute', request);
      return response.data;
    } catch (error) {
      console.error('Agent execution failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Agent 상태 조회
   */
  async getAgentStatus(agentType: string): Promise<AgentResponse> {
    try {
      const response = await this.client.get(`/status/${agentType}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get agent status:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * 모든 Agent 상태 조회
   */
  async getAllAgentsStatus(): Promise<AgentResponse> {
    try {
      const response = await this.client.get('/status');
      return response.data;
    } catch (error) {
      console.error('Failed to get all agents status:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Agent 헬스체크
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('Agent health check failed:', error);
      return false;
    }
  }
}

// 싱글톤 인스턴스
export const agentClient = new AgentClient();

export default agentClient;
