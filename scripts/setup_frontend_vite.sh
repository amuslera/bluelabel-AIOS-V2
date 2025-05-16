#!/bin/bash

# Setup script for Bluelabel AIOS Frontend with Vite

echo "🚀 Setting up Bluelabel AIOS Frontend with Vite..."

# Navigate to the apps directory
cd "$(dirname "$0")/../apps" || exit

# Backup existing ui directory
if [ -d "ui" ]; then
    echo "⚠️  Backing up existing ui directory..."
    mv ui ui_backup_$(date +%Y%m%d_%H%M%S)
fi

# Create Vite React app with TypeScript
echo "📦 Creating Vite React app with TypeScript..."
npm create vite@latest ui -- --template react-ts

# Navigate to ui directory
cd ui || exit

# Install dependencies
echo "📚 Installing dependencies..."
npm install

# Install additional dependencies
npm install \
  react-router-dom@latest \
  axios@latest \
  @tanstack/react-query@latest \
  socket.io-client@latest \
  framer-motion@latest \
  zustand@latest

# Install UI dependencies
npm install \
  tailwindcss@latest \
  @tailwindcss/forms@latest \
  @tailwindcss/typography@latest \
  autoprefixer@latest \
  postcss@latest

# Initialize Tailwind
npx tailwindcss init -p

# Install types
npm install -D \
  @types/react@latest \
  @types/react-dom@latest \
  @types/node@latest

echo "✅ Vite frontend setup complete!"
echo ""
echo "To start the development server:"
echo "  cd apps/ui"
echo "  npm run dev"
echo ""
echo "The app will be available at http://localhost:5173"