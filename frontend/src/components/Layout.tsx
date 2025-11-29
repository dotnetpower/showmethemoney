import { ReactNode } from "react";
import { useTheme } from "../context/ThemeContext";

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Show Me The Dollar</h1>
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="테마 전환"
          >
            {theme === "light" ? "🌙" : "☀️"}
          </button>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
};

export default Layout;
