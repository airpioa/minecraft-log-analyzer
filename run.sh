#!/bin/bash
set -e

# Minecraft Log Analyzer - Web Runner
echo "🚀 Starting Minecraft Log Analyzer Web..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install || { echo "❌ Failed to install dependencies. Try running 'npm install --force' manually."; exit 1; }
fi

# Start the development server
echo "✨ Launching development server..."
npm run dev
