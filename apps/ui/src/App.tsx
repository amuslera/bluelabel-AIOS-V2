import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Dashboard } from './features/dashboard/Dashboard';
import { TerminalPage } from './features/terminal/TerminalPage';
import { Inbox } from './features/inbox/Inbox';
import { Knowledge } from './features/knowledge/Knowledge';
import { Agents } from './features/agents/Agents';
import { Logs } from './features/logs/Logs';
import { ROIWorkflowContainer } from './components/ROIWorkflow/ROIWorkflowContainer';
import { StartupSequence } from './components/UI/StartupSequence';
import { NavigationWrapper } from './components/Navigation/NavigationWrapper';
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

  return (
    <Router>
      <div className={`transition-opacity duration-500 ${showMain ? 'opacity-100' : 'opacity-0'}`}>
        <NavigationWrapper>
          {/* Main content with padding */}
          <div className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inbox" element={<Inbox />} />
              <Route path="/knowledge" element={<Knowledge />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/terminal" element={<TerminalPage />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/roi-workflow" element={<ROIWorkflowContainer />} />
              <Route path="/settings" element={
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">⚙️</div>
                  <h2 className="text-2xl font-terminal text-terminal-cyan mb-4 uppercase">
                    System Configuration
                  </h2>
                  <p className="text-terminal-cyan/70 mb-8">
                    Settings panel coming soon...
                  </p>
                  <div className="inline-block px-6 py-3 border border-terminal-cyan text-terminal-cyan font-terminal uppercase hover:bg-terminal-cyan/10 transition-colors rounded-lg">
                    Under Development
                  </div>
                </div>
              } />
            </Routes>
          </div>
        </NavigationWrapper>
      </div>
    </Router>
  );
}

export default App;