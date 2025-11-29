import { createContext, ReactNode, useContext } from "react";
import { DashboardDataset, useEtfData } from "../hooks/useEtfData";

interface DataContextValue extends DashboardDataset {
  loading: boolean;
}

const defaultValue: DataContextValue = {
  loading: false,
  etfs: [],
  dividendByWeekday: [],
  dividendByMonth: [],
  totalReturnSeries: [],
};

const DataContext = createContext<DataContextValue>(defaultValue);

export const DataProvider = ({ children }: { children: ReactNode }) => {
  const { data, loading } = useEtfData();

  return (
    <DataContext.Provider value={{ ...data, loading }}>
      {children}
    </DataContext.Provider>
  );
};

export const useDashboardData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error("useDashboardData must be used within DataProvider");
  }
  return context;
};
