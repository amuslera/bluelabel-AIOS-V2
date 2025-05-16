import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Dashboard } from './features/dashboard/Dashboard';
import { TerminalPage } from './features/terminal/TerminalPage';
import { Inbox } from './features/inbox/Inbox';
import { Knowledge } from './features/knowledge/Knowledge';
import { Agents } from './features/agents/Agents';
import { Logs } from './features/logs/Logs';
import { StartupSequence } from './components/UI/StartupSequence';
import { RainbowStripe } from './components/UI/RainbowStripe';
import { PixelLogo } from './components/UI/PixelLogo';
import { WebSocketIndicator } from './components/UI/WebSocketIndicator';
import { appConfig } from './config/app.config';
import './App.css';

function App() {
  const [showStartup, setShowStartup] = useState(true);
  const [showMain, setShowMain] = useState(false);

  const handleStartupComplete = () => {
    setShowStartup(false);
    setTimeout(() => setShowMain(true), 100);
  };

  if (showStartup) {
    return <StartupSequence onComplete={handleStartupComplete} />;
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 font-terminal text-lg uppercase transition-all duration-200 ${
      isActive 
        ? 'text-terminal-cyan border-b-2 border-terminal-cyan' 
        : 'text-terminal-cyan/70 hover:text-terminal-cyan'
    }`;

  return (
    <Router>
      <div className={`min-h-screen bg-terminal-bg text-terminal-cyan font-terminal transition-opacity duration-500 ${showMain ? 'opacity-100' : 'opacity-0'}`}>
        <div className="container mx-auto px-4">
          <header className="py-6">
            <div className="flex justify-between items-center">
              <div className="flex-1 flex justify-center">
                <div className="flex flex-col items-center">
                  <div className="mb-3">
                    <PixelLogo />
                  </div>
                  <div className="text-base text-terminal-cyan/90">
                    AIOS v2 BOOTED. AWAITING INPUT.
                  </div>
                </div>
              </div>
              {appConfig.websocket.enabled && (
                <div className="absolute right-4">
                  <WebSocketIndicator />
                </div>
              )}
            </div>
          </header>
          
          <nav className="py-4 border-b-2 border-terminal-cyan flex flex-wrap gap-2 justify-center">
            <NavLink to="/" className={navLinkClass}>
              [DASHBOARD]
            </NavLink>
            <NavLink to="/inbox" className={navLinkClass}>
              [INBOX]
            </NavLink>
            <NavLink to="/knowledge" className={navLinkClass}>
              [KNOWLEDGE]
            </NavLink>
            <NavLink to="/agents" className={navLinkClass}>
              [AGENTS]
            </NavLink>
            <NavLink to="/terminal" className={navLinkClass}>
              [TERMINAL]
            </NavLink>
            <NavLink to="/logs" className={navLinkClass}>
              [LOGS]
            </NavLink>
            <NavLink to="/settings" className={navLinkClass}>
              [SETTINGS]
            </NavLink>
          </nav>
          
          <RainbowStripe />
          
          <main className="py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inbox" element={<Inbox />} />
              <Route path="/knowledge" element={<Knowledge />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/terminal" element={<TerminalPage />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/settings" element={<div className="text-xl text-center">Settings - Coming Soon</div>} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;