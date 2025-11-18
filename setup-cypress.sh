#!/bin/bash
# Setup script for Cypress testing

echo "🚀 Setting up Cypress for KAM Automation Testing..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js v14+ from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Install dependencies
echo "📦 Installing Cypress and dependencies..."
npm install

# Create cypress.env.json if it doesn't exist
if [ ! -f "cypress.env.json" ]; then
    echo "📝 Creating cypress.env.json from example..."
    cp cypress.env.example.json cypress.env.json
    echo "⚠️  Please edit cypress.env.json with your test credentials!"
else
    echo "✅ cypress.env.json already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit cypress.env.json with your test credentials"
echo "2. Start your Streamlit app: streamlit run Homepage.py"
echo "3. Run tests: npm run cypress:open"
echo ""

