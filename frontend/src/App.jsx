import React, { useState, useMemo, useCallback, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import AuthPage from "./components/AuthPage";
import Dashboard from "./pages/Dashboard";
import EditorPage from "./pages/Editor";
import Activity from "./pages/Activity";
import Profile from "./pages/Profile";
import About from "./pages/About";
import { LogOut, Home, Code, Activity as ActivityIcon, User, Info, Sun, Moon } from "lucide-react";

function Navigation({ user, onLogout }) {
  const [isLight, setIsLight] = useState(() => document.documentElement.classList.contains('light-theme'));
  
  const toggleTheme = () => {
    document.documentElement.classList.toggle('light-theme');
    setIsLight(!isLight);
  };

  const location = useLocation();
  const navItems = [
    { path: "/", label: "Dashboard", icon: <Home size={18} /> },
    { path: "/editor", label: "Editor", icon: <Code size={18} /> },
    { path: "/activity", label: "Activity", icon: <ActivityIcon size={18} /> },
    { path: "/profile", label: "Profile", icon: <User size={18} /> },
    { path: "/about", label: "About", icon: <Info size={18} /> },
  ];

  return (
    <nav className="sidebar h-screen bg-[var(--bg-secondary)] w-64 flex flex-col fixed left-0 top-0 border-r border-[var(--border)]">
      <div className="p-6 border-b border-[var(--border)]">
        <h1 className="text-xl font-bold tracking-wide text-[var(--text-primary)]">CodeConcept</h1>
        <div className="text-xs text-blue-500 mt-1">AI Learning Engine</div>
      </div>
      
      <div className="flex-1 py-6 flex flex-col gap-2 px-4">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === item.path 
                ? "bg-blue-600/10 text-blue-500 border border-blue-500/20 shadow-sm" 
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
            }`}
          >
            {item.icon}
            <span className="font-medium">{item.label}</span>
          </Link>
        ))}
      </div>

      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-3 px-4 py-2 mb-2 text-[var(--text-primary)]">
          <div className="w-8 h-8 rounded-full bg-[var(--bg-card)] border border-[var(--border)] flex items-center justify-center font-bold text-blue-500">
            {user?.name?.[0]?.toUpperCase()}
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">{user.name}</span>
            <span className="text-xs text-[var(--text-secondary)]">{user.level}</span>
          </div>
        </div>
        
        <button 
          onClick={toggleTheme}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-yellow-500 hover:bg-yellow-500/10 rounded-lg transition-colors mb-2"
        >
          {isLight ? <Moon size={16} /> : <Sun size={16} />}
          {isLight ? "Dark Mode" : "Light Mode"}
        </button>

        <button 
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </nav>
  );
}

import ErrorBoundary from "./components/ErrorBoundary";

function MainApp({ user, token, handleLogout }) {
  return (
    <div className="flex min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans">
      <Navigation user={user} onLogout={handleLogout} />
      <main className="flex-1 ml-64 min-h-screen relative overflow-x-hidden">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard user={user} token={token} />} />
            <Route path="/editor" element={<EditorPage user={user} token={token} handleLogout={handleLogout} />} />
            <Route path="/activity" element={<Activity user={user} />} />
            <Route path="/profile" element={<Profile user={user} />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("cc_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem("cc_token"));

  const isAuthenticated = !!(user && token);

  const handleAuth = useCallback((userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    localStorage.setItem("cc_user", JSON.stringify(userData));
    localStorage.setItem("cc_token", accessToken);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("cc_token");
    localStorage.removeItem("cc_user");
    setUser(null);
    setToken(null);
  }, []);

  return (
    <BrowserRouter>
      {!isAuthenticated ? (
        <AuthPage onAuth={handleAuth} />
      ) : (
        <MainApp user={user} token={token} handleLogout={handleLogout} />
      )}
    </BrowserRouter>
  );
}

export default App;
