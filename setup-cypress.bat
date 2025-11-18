@echo off
REM Setup script for Cypress testing (Windows)

echo 🚀 Setting up Cypress for KAM Automation Testing...

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js v14+ from https://nodejs.org/
    exit /b 1
)

echo ✅ Node.js version:
node --version

REM Install dependencies
echo 📦 Installing Cypress and dependencies...
call npm install

REM Create cypress.env.json if it doesn't exist
if not exist "cypress.env.json" (
    echo 📝 Creating cypress.env.json from example...
    copy cypress.env.example.json cypress.env.json
    echo ⚠️  Please edit cypress.env.json with your test credentials!
) else (
    echo ✅ cypress.env.json already exists
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit cypress.env.json with your test credentials
echo 2. Start your Streamlit app: streamlit run Homepage.py
echo 3. Run tests: npm run cypress:open
echo.

pause

