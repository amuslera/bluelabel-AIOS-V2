import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Dashboard } from './features/dashboard/Dashboard';
import { TerminalPage } from './features/terminal/TerminalPage';
import { StartupSequence } from './components/UI/StartupSequence';
import { RainbowStripe } from './components/UI/RainbowStripe';
import { PixelLogo } from './components/UI/PixelLogo';
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
    `px-4 py-2 font-terminal uppercase transition-all duration-200 ${
      isActive 
        ? 'text-terminal-cyan border-b-2 border-terminal-cyan retro-glow' 
        : 'text-terminal-cyan/70 hover:text-terminal-cyan hover:retro-glow'
    }`;

  return (
    <Router>
      <div className={`min-h-screen bg-terminal-bg text-terminal-cyan font-terminal transition-opacity duration-500 ${showMain ? 'opacity-100' : 'opacity-0'}`}>
        <RainbowStripe />
        
        <div className="container mx-auto px-4">
          <header className="py-8 text-center">
            <PixelLogo />
            <div className="text-lg mt-4 text-terminal-cyan retro-glow">
              AIOS v2 BOOTED. AWAITING INPUT.
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
          
          <main className="py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inbox" element={<div className="text-xl text-center">Inbox - Coming Soon</div>} />
              <Route path="/knowledge" element={<div className="text-xl text-center">Knowledge - Coming Soon</div>} />
              <Route path="/agents" element={<div className="text-xl text-center">Agents - Coming Soon</div>} />
              <Route path="/terminal" element={<TerminalPage />} />
              <Route path="/logs" element={<div className="text-xl text-center">Logs - Coming Soon</div>} />
              <Route path="/settings" element={<div className="text-xl text-center">Settings - Coming Soon</div>} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;