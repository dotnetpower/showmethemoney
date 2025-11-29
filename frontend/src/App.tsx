import DashboardPage from "./pages/Dashboard";
import { DataProvider } from "./context/DataContext";

function App() {
  return (
    <DataProvider>
      <DashboardPage />
    </DataProvider>
  );
}

export default App;
