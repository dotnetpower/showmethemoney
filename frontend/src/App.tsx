import { useState } from "react";
import DashboardPage from "./pages/Dashboard";
import { DataProvider } from "./context/DataContext";
import { ThemeProvider } from "./context/ThemeContext";
import Layout from "./components/Layout";
import Navigation from "./components/Navigation";
import EtfList from "./components/EtfList";
import DividendSchedule from "./components/DividendSchedule";
import TotalReturnSection from "./components/TotalReturnSection";
import DividendSimulator from "./components/DividendSimulator";

function App() {
  const [currentView, setCurrentView] = useState("etf-list");

  const renderView = () => {
    switch (currentView) {
      case "etf-list":
        return <EtfList />;
      case "dividend-schedule":
        return <DividendSchedule />;
      case "dividend-simulator":
        return <DividendSimulator />;
      case "total-return":
        return <TotalReturnSection />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <ThemeProvider>
      <DataProvider>
        <Layout>
          <Navigation currentView={currentView} onViewChange={setCurrentView} />
          <div className="content-area">{renderView()}</div>
        </Layout>
      </DataProvider>
    </ThemeProvider>
  );
}

export default App;
