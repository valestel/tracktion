import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import logoDark from "./assets/logo-dark.png";
import logoLight from "./assets/logo-light.png";
import { ThemeToggle } from "./components/common/ThemeToggle";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { DashboardPage } from "./pages/DashboardPage";
import "./styles/theme.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <div className="app-layout">
            <nav className="app-nav">
              <Link to="/" className="logo">
                <img src={logoLight} alt="" className="logo-img logo-img--light" />
                <img src={logoDark} alt="" className="logo-img logo-img--dark" />
                Tracktion
              </Link>
              <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
                Applications
              </NavLink>
              <NavLink
                to="/dashboard"
                className={({ isActive }) => (isActive ? "active" : "")}
              >
                Dashboard
              </NavLink>
              <ThemeToggle />
            </nav>

            <main className="app-content">
              <Routes>
                <Route path="/" element={<ApplicationsPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
