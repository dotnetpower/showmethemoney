import { useEffect, useState } from "react";
import { fetchUsers } from "../services/userApi";

export interface DashboardDataset {
  etfs: Array<{
    ticker: string;
    price: number;
    dividendYield: number;
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
      price: 560.22,
      dividendYield: 0.014,
      marketCap: 450_000_000_000,
    },
    {
      ticker: "QQQ",
      price: 482.12,
      dividendYield: 0.009,
      marketCap: 220_000_000_000,
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
