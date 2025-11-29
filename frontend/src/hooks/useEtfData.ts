import { useEffect, useState } from "react";
import { fetchUsers } from "../services/userApi";

export interface DashboardDataset {
  etfs: Array<{
    ticker: string;
    nameKr: string;
    price: number;
    priceChange: number;
    priceChangePercent: number;
    dividendYield: number;
    lastDividendDate: string;
    marketCap: number;
  }>;
  dividendByWeekday: Array<{ day: string; symbols: string[] }>;
  dividendByMonth: Array<{ month: string; symbols: string[] }>;
  totalReturnSeries: Array<{ date: string; value: number }>;
}

const defaultData: DashboardDataset = {
  etfs: [
    {
      ticker: "SPY",
      nameKr: "S&P 500 ETF",
      price: 560.22,
      priceChange: 5.32,
      priceChangePercent: 0.96,
      dividendYield: 0.014,
      lastDividendDate: "2024-12-20",
      marketCap: 450_000_000_000,
    },
    {
      ticker: "QQQ",
      nameKr: "나스닥 100 ETF",
      price: 482.12,
      priceChange: -2.15,
      priceChangePercent: -0.44,
      dividendYield: 0.009,
      lastDividendDate: "2024-12-18",
      marketCap: 220_000_000_000,
    },
    {
      ticker: "JEPI",
      nameKr: "JP모건 주식 프리미엄 인컴",
      price: 58.45,
      priceChange: 0.12,
      priceChangePercent: 0.21,
      dividendYield: 0.074,
      lastDividendDate: "2024-12-23",
      marketCap: 35_000_000_000,
    },
  ],
  dividendByWeekday: [
    { day: "월", symbols: ["SPY", "JEPI"] },
    { day: "화", symbols: ["QQQ", "VTI"] },
  ],
  dividendByMonth: [
    { month: "1월", symbols: ["SPY"] },
    { month: "2월", symbols: ["QQQ"] },
  ],
  totalReturnSeries: [
    { date: "2024-01", value: 100 },
    { date: "2024-06", value: 112 },
    { date: "2024-11", value: 126 },
  ],
};

export const useEtfData = () => {
  const [data, setData] = useState<DashboardDataset>(defaultData);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const users = await fetchUsers();
        if (users.length) {
          setData((prev: DashboardDataset) => ({
            ...prev,
            dividendByWeekday: prev.dividendByWeekday.map((item) => ({
              ...item,
              symbols: Array.from(
                new Set([...item.symbols, ...users[0].favorite_etfs])
              ),
            })),
          }));
        }
      } catch (error) {
        console.warn("사용자 데이터를 불러오지 못했습니다", error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  return { data, loading };
};
