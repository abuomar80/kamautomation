describe('Z39.50 Configuration Tests', () => {
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

  it('should navigate to Z39.50 page', () => {
    cy.contains('Z39.50', { matchCase: false }).click()
    cy.waitForStreamlit()
    cy.contains('Z39.5', { matchCase: false }).should('be.visible')
  })

  it('should display Z39.50 server selection', () => {
    cy.contains('Z39.50', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Check for multiselect dropdown
    cy.contains('Please choose Profiles to create', { matchCase: false }).should('be.visible')
  })

  it('should show available Z39.50 servers', () => {
    cy.contains('Z39.50', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Check for some common server names
    cy.contains('Library of Congress', { matchCase: false }).should('be.visible')
    cy.contains('OCLC', { matchCase: false }).should('be.visible')
  })

  it('should display create button', () => {
    cy.contains('Z39.50', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    cy.contains('button', 'Create', { matchCase: false }).should('exist')
  })
})

