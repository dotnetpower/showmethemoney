import DividendSchedule from "../components/DividendSchedule";
import EtfList from "../components/EtfList";
import TotalReturnSection from "../components/TotalReturnSection";

const DashboardPage = () => {
  return (
    <main className="layout">
      <header>
        <h1>show-me-the-money</h1>
        <p>ETF 및 주식 데이터를 한눈에 파악하세요.</p>
      </header>
      <section className="grid">
        <EtfList />
        <DividendSchedule />
        <TotalReturnSection />
      </section>
    </main>
  );
};

export default DashboardPage;
