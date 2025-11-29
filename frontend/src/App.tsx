import { useState, useEffect } from "react";
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

  // 스크롤 시 테이블 헤더가 메인 헤더와 만나면 메인 헤더 숨기기
  useEffect(() => {
    const handleScroll = () => {
      const tableHeader = document.querySelector(".etf-table thead");
      if (!tableHeader) return;

      const headerRect = tableHeader.getBoundingClientRect();
      const appHeaderHeight = 64; // CSS의 --app-header-height와 동일

      // 테이블 헤더가 화면 상단 근처에 있으면 메인 헤더 숨김
      if (headerRect.top <= appHeaderHeight) {
        document.documentElement.classList.add("hide-app-header");
      } else {
        document.documentElement.classList.remove("hide-app-header");
      }
    };

    window.addEventListener("scroll", handleScroll);
    handleScroll(); // 초기 상태 확인

    return () => window.removeEventListener("scroll", handleScroll);
  }, [currentView]);

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
