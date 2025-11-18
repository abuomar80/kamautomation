# Cypress Testing Guide

This project uses Cypress for end-to-end testing of the Streamlit application.

## 📋 Prerequisites

1. **Node.js** (v14 or higher) - [Download Node.js](https://nodejs.org/)
2. **Streamlit application running** on `http://localhost:8501`

## 🚀 Setup

### 1. Install Dependencies

```bash
npm install
```

This will install Cypress and other testing dependencies.

### 2. Configure Test Credentials

Copy the example environment file and fill in your test credentials:

```bash
cp cypress.env.example.json cypress.env.json
```

Edit `cypress.env.json` with your test credentials:

```json
{
  "TEST_USERNAME": "your_test_username",
  "TEST_PASSWORD": "your_test_password",
  "TENANT_USERNAME": "your_tenant_username",
  "TENANT_PASSWORD": "your_tenant_password",
  "TENANT_NAME": "your_tenant_name",
  "OKAPI_URL": "https://okapi.medad.com"
}
```

**⚠️ Important:** `cypress.env.json` is in `.gitignore` and should NOT be committed to version control.

### 3. Start Your Streamlit Application

Before running tests, make sure your Streamlit app is running:

```bash
streamlit run Homepage.py
```

The application should be accessible at `http://localhost:8501`

## 🧪 Running Tests

### Open Cypress Test Runner (Interactive Mode)

```bash
npm run cypress:open
```

This opens the Cypress Test Runner GUI where you can:
- See all test files
- Run tests interactively
- Watch tests execute in real-time
- Debug tests easily

### Run Tests Headlessly (CI/CD Mode)

```bash
npm run cypress:run
```

This runs all tests in headless mode (no browser window). Perfect for:
- CI/CD pipelines
- Quick test runs
- Automated testing

### Run Tests with Browser Visible

```bash
npm run test:headed
```

This runs tests with the browser visible (useful for debugging).

## 📁 Test Structure

```
cypress/
├── e2e/                    # Test files
│   ├── homepage.cy.js      # Homepage and authentication tests
│   ├── tenant-connection.cy.js  # Tenant connection tests
│   └── advanced-configuration.cy.js  # Advanced configuration tests
├── fixtures/               # Test data
│   └── example.json
├── support/                # Support files
│   ├── commands.js         # Custom Cypress commands
│   └── e2e.js              # Global configuration
└── screenshots/            # Screenshots (auto-generated)
└── videos/                 # Test videos (auto-generated)
```

## 🛠️ Custom Commands

The project includes custom Cypress commands for common operations:

### `cy.login(username, password)`
Logs into the Streamlit application.

```javascript
cy.login('kam', 'password123')
```

### `cy.connectToTenant(tenantConfig)`
Connects to a FOLIO tenant.

```javascript
cy.connectToTenant({
  username: 'tenant_user',
  password: 'tenant_pass',
  tenantName: 'kam_new',
  okapiUrl: 'https://okapi.medad.com'
})
```

### `cy.waitForStreamlit()`
Waits for Streamlit to finish loading.

```javascript
cy.waitForStreamlit()
```

## ✍️ Writing New Tests

### Example Test File

Create a new test file in `cypress/e2e/`:

```javascript
describe('My Feature Tests', () => {
  beforeEach(() => {
    // Login before each test
    cy.login(Cypress.env('TEST_USERNAME'), Cypress.env('TEST_PASSWORD'))
    cy.waitForStreamlit()
  })

  it('should test my feature', () => {
    // Navigate to page
    cy.contains('My Page').click()
    cy.waitForStreamlit()
    
    // Interact with elements
    cy.get('input[type="text"]').type('test value')
    cy.contains('button', 'Submit').click()
    
    // Assert results
    cy.contains('Success').should('be.visible')
  })
})
```

## 🔧 Configuration

The Cypress configuration is in `cypress.config.js`. Key settings:

- **baseUrl**: `http://localhost:8501` (Streamlit default port)
- **viewportWidth**: 1280px
- **viewportHeight**: 720px
- **video**: Enabled (records test videos)
- **screenshotOnRunFailure**: Enabled

## 📝 Test Coverage

Current test coverage includes:

1. **Homepage Tests** (`homepage.cy.js`)
   - Homepage loading
   - Login form display
   - Invalid credentials handling

2. **Tenant Connection Tests** (`tenant-connection.cy.js`)
   - Navigation to tenant page
   - Form display
   - Validation errors

3. **Advanced Configuration Tests** (`advanced-configuration.cy.js`)
   - Page navigation
   - Template download
   - Tab navigation
   - Loan Policies section

## 🐛 Debugging

### View Test Videos

After running tests, videos are saved in `cypress/videos/` directory.

### View Screenshots

Screenshots on failure are saved in `cypress/screenshots/` directory.

### Debug in Browser

1. Open Cypress Test Runner: `npm run cypress:open`
2. Click on a test file
3. Use `cy.pause()` in your test to pause execution
4. Use browser DevTools to inspect elements

## 🔒 Security Notes

- Never commit `cypress.env.json` (contains credentials)
- Use environment variables for sensitive data
- Consider using separate test accounts for testing

## 📚 Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Streamlit Testing Guide](https://docs.streamlit.io/develop/concepts/architecture)

## 🤝 Contributing

When adding new features:
1. Write corresponding Cypress tests
2. Ensure tests pass before submitting PR
3. Update this README if adding new test categories

