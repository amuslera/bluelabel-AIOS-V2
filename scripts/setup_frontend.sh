#!/bin/bash

# Setup script for Bluelabel AIOS Frontend

echo "🚀 Setting up Bluelabel AIOS Frontend..."

# Navigate to the apps directory
cd "$(dirname "$0")/../apps" || exit

# Remove existing ui directory if it exists
if [ -d "ui" ]; then
    echo "⚠️  Removing existing ui directory..."
    rm -rf ui
fi

# Create React app with TypeScript
echo "📦 Creating React app with TypeScript..."
npx create-react-app ui --template typescript

# Navigate to ui directory
cd ui || exit

# Install Tailwind CSS and dependencies
echo "🎨 Installing Tailwind CSS..."
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install additional dependencies
echo "📚 Installing additional dependencies..."
npm install \
  react-router-dom \
  zustand \
  axios \
  react-query \
  socket.io-client \
  framer-motion \
  @types/react-router-dom \
  @types/node

# Install retro terminal fonts and UI components
npm install \
  react-terminal-ui \
  react-typed

# Install development dependencies
npm install -D \
  @types/react \
  @types/react-dom \
  prettier \
  eslint-config-prettier \
  eslint-plugin-prettier

# Install shadcn/ui CLI
echo "🎨 Setting up shadcn/ui..."
npx shadcn-ui@latest init -y

# Create directory structure
echo "📁 Creating project structure..."
mkdir -p src/{api,components/{Layout,Terminal,UI},features/{dashboard,inbox,knowledge,agents,terminal},hooks,store,styles,types,utils}

# Setup Tailwind configuration for retro theme
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'midnight-blue': '#0B0F1D',
        'dark-navy': '#060914',
        'cyan': '#7FFFD4',
        'bright-cyan': '#B0FFE9',
        'dark-cyan': '#4FE6C4',
        'success-green': '#00FF00',
        'error-pink': '#FF0080',
        'warning-gold': '#FFD700',
        'processing-blue': '#00BFFF',
      },
      fontFamily: {
        'terminal': ['VT323', 'monospace'],
        'mono': ['IBM Plex Mono', 'monospace'],
      },
      animation: {
        'blink': 'blink 0.75s step-end infinite',
        'typing': 'typing 3.5s steps(40, end)',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        blink: {
          'from, to': { opacity: '0' },
          '50%': { opacity: '1' },
        },
        typing: {
          'from': { width: '0' },
          'to': { width: '100%' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 5px currentColor' },
          '50%': { boxShadow: '0 0 20px currentColor, 0 0 30px currentColor' },
        },
      },
    },
  },
  plugins: [],
}
EOF

# Create base CSS file
cat > src/index.css << 'EOF'
@import url('https://fonts.googleapis.com/css2?family=VT323&family=IBM+Plex+Mono:wght@400;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-midnight-blue text-cyan font-terminal;
    font-size: 16px;
    line-height: 1.5;
  }
  
  /* Retro CRT effect */
  .crt::before {
    content: " ";
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    background: linear-gradient(
      rgba(18, 16, 16, 0) 50%,
      rgba(0, 0, 0, 0.25) 50%
    );
    background-size: 100% 4px;
    z-index: 2;
    pointer-events: none;
  }
  
  /* Retro glow effect */
  .retro-glow {
    text-shadow: 
      0 0 5px currentColor,
      0 0 10px currentColor,
      0 0 15px currentColor;
  }
}

/* ASCII borders */
.ascii-border {
  border-style: solid;
  border-width: 2px;
  box-shadow: 
    2px 2px 0px 0px rgba(127, 255, 212, 0.3),
    4px 4px 0px 0px rgba(127, 255, 212, 0.2);
}

/* Cursor animation */
.cursor::after {
  content: '_';
  display: inline-block;
  animation: blink 0.75s step-end infinite;
  color: #7FFFD4;
}
EOF

# Create environment variables template
cat > .env.example << 'EOF'
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
EOF

# Copy environment file
cp .env.example .env

# Create base App component
cat > src/App.tsx << 'EOF'
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-midnight-blue text-cyan font-terminal crt">
        <div className="container mx-auto px-4">
          <header className="py-4 border-b-2 border-cyan">
            <h1 className="text-2xl font-bold retro-glow">
              BLUELABEL AIOS v2.0
            </h1>
          </header>
          <main className="py-8">
            <Routes>
              <Route path="/" element={<div>Dashboard</div>} />
              <Route path="/inbox" element={<div>Inbox</div>} />
              <Route path="/knowledge" element={<div>Knowledge</div>} />
              <Route path="/agents" element={<div>Agents</div>} />
              <Route path="/terminal" element={<div>Terminal</div>} />
              <Route path="/logs" element={<div>Logs</div>} />
              <Route path="/settings" element={<div>Settings</div>} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
EOF

# Create basic type definitions
cat > src/types/index.ts << 'EOF'
export interface SystemStatus {
  status: 'online' | 'offline' | 'warning';
  components: {
    [key: string]: {
      status: 'ok' | 'error' | 'warning';
      lastCheck: string;
    };
  };
}

export interface InboxItem {
  id: string;
  type: 'email' | 'whatsapp' | 'manual';
  from: string;
  subject: string;
  time: string;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  hasCodeword?: boolean;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  type: string;
  source: string;
  created: string;
  tags: string[];
  preview: string;
}

export interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  lastActivity: string;
  tasksCompleted: number;
  tasksFailed: number;
  averageProcessingTime: number;
}
EOF

# Create API client
cat > src/api/client.ts << 'EOF'
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth (future)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
EOF

# Create a basic retro button component
mkdir -p src/components/UI
cat > src/components/UI/RetroButton.tsx << 'EOF'
import React from 'react';

interface RetroButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'error' | 'warning';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export const RetroButton: React.FC<RetroButtonProps> = ({
  children,
  variant = 'primary',
  onClick,
  disabled = false,
  className = '',
}) => {
  const variants = {
    primary: 'border-cyan text-cyan hover:bg-cyan/10',
    success: 'border-success-green text-success-green hover:bg-success-green/10',
    error: 'border-error-pink text-error-pink hover:bg-error-pink/10',
    warning: 'border-warning-gold text-warning-gold hover:bg-warning-gold/10',
  };

  return (
    <button
      className={`
        px-4 py-2 border-2 font-terminal uppercase
        transition-all duration-200
        ${variants[variant]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        shadow-[2px_2px_0px_0px_rgba(127,255,212,0.3)]
        hover:shadow-[4px_4px_0px_0px_rgba(127,255,212,0.5)]
        active:transform active:translate-y-0.5
        ${className}
      `}
      onClick={onClick}
      disabled={disabled}
    >
      [{children}]
    </button>
  );
};
EOF

# Create package.json scripts
npm pkg set scripts.start="react-scripts start"
npm pkg set scripts.build="react-scripts build"
npm pkg set scripts.test="react-scripts test"
npm pkg set scripts.eject="react-scripts eject"
npm pkg set scripts.format="prettier --write \"src/**/*.{js,jsx,ts,tsx,json,css,md}\""
npm pkg set scripts.lint="eslint src --ext .js,.jsx,.ts,.tsx"

echo "✅ Frontend setup complete!"
echo ""
echo "To start the development server:"
echo "  cd apps/ui"
echo "  npm start"
echo ""
echo "The app will be available at http://localhost:3000"