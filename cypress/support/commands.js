// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

/**
 * Custom command to login to the Streamlit application
 * @param {string} username - Username for authentication
 * @param {string} password - Password for authentication
 */
Cypress.Commands.add('login', (username, password) => {
  cy.visit('/')
  
  // Wait for login form to be visible
  cy.get('input[type="text"], input[name*="username"], input[placeholder*="Username"]').first().should('be.visible')
  
  // Fill in username
  cy.get('input[type="text"], input[name*="username"], input[placeholder*="Username"]').first().type(username)
  
  // Fill in password
  cy.get('input[type="password"]').first().type(password)
  
  // Click login button
  cy.contains('button', 'Login', { matchCase: false }).click()
  
  // Wait for login to complete (check for logout button or welcome message)
  cy.contains('Logout', { timeout: 10000 }).should('exist').or(cy.contains('Welcome', { timeout: 10000 }))
})

/**
 * Custom command to connect to a tenant
 * @param {object} tenantConfig - Configuration object with tenant details
 */
Cypress.Commands.add('connectToTenant', (tenantConfig) => {
  const { username, password, tenantName, okapiUrl } = tenantConfig
  
  // Navigate to tenant page if not already there
  cy.visit('/')
  cy.contains('Tenant', { matchCase: false }).click()
  
  // Fill in tenant connection form
  cy.get('input[placeholder*="Username"], input[name*="username"]').first().type(username)
  cy.get('input[type="password"]').first().type(password)
  cy.get('input[placeholder*="Tenant"], input[name*="tenant"]').first().type(tenantName)
  
  // Select Okapi URL from dropdown
  if (okapiUrl) {
    cy.get('select, [role="combobox"]').first().select(okapiUrl)
  }
  
  // Click connect button
  cy.contains('button', 'Connect', { matchCase: false }).click()
  
  // Wait for success message
  cy.contains('Connected', { matchCase: false, timeout: 15000 }).should('be.visible')
})

/**
 * Custom command to wait for Streamlit to finish loading
 */
Cypress.Commands.add('waitForStreamlit', () => {
  // Streamlit shows a loading indicator, wait for it to disappear
  cy.get('[data-testid="stAppViewContainer"]', { timeout: 10000 }).should('exist')
  // Wait a bit more for any dynamic content to load
  cy.wait(1000)
})

