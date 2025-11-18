describe('Advanced Configuration Tests', () => {
  beforeEach(() => {
    // Login and connect to tenant
    cy.login(Cypress.env('TEST_USERNAME') || 'kam', Cypress.env('TEST_PASSWORD') || 'test')
    cy.waitForStreamlit()
    
    // Connect to tenant if credentials are provided
    if (Cypress.env('TENANT_USERNAME')) {
      cy.connectToTenant({
        username: Cypress.env('TENANT_USERNAME'),
        password: Cypress.env('TENANT_PASSWORD'),
        tenantName: Cypress.env('TENANT_NAME'),
        okapiUrl: Cypress.env('OKAPI_URL')
      })
    }
  })

  it('should navigate to Advanced Configuration page', () => {
    cy.contains('Advanced Configuration', { matchCase: false }).click()
    cy.waitForStreamlit()
    cy.contains('Advanced Configuration', { matchCase: false }).should('be.visible')
  })

  it('should display template download section', () => {
    cy.contains('Advanced Configuration', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    cy.contains('Download Excel Template', { matchCase: false }).should('be.visible')
    cy.contains('button', 'Download', { matchCase: false }).should('exist')
  })

  it('should display all configuration tabs', () => {
    cy.contains('Advanced Configuration', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Check for main tabs
    cy.contains('Upload', { matchCase: false }).should('be.visible')
    cy.contains('Material Types', { matchCase: false }).should('be.visible')
    cy.contains('Statistical Codes', { matchCase: false }).should('be.visible')
  })

  it('should show Loan Policies tab with data validation', () => {
    cy.contains('Advanced Configuration', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    cy.contains('Loan Policies', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Check for loan policies content
    cy.contains('Loan Policies', { matchCase: false }).should('be.visible')
  })
})

