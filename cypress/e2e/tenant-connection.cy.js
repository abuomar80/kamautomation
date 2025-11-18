describe('Tenant Connection Tests', () => {
  beforeEach(() => {
    // Login first (adjust credentials as needed)
    cy.login(Cypress.env('TEST_USERNAME') || 'kam', Cypress.env('TEST_PASSWORD') || 'test')
    cy.waitForStreamlit()
  })

  it('should navigate to tenant page', () => {
    cy.contains('Tenant', { matchCase: false }).click()
    cy.url().should('include', 'Tenant')
    cy.waitForStreamlit()
  })

  it('should display tenant connection form', () => {
    cy.contains('Tenant', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Check for form fields
    cy.get('input[type="text"], input[type="password"]').should('have.length.at.least', 3)
    cy.contains('button', 'Connect', { matchCase: false }).should('exist')
  })

  it('should show error for missing tenant information', () => {
    cy.contains('Tenant', { matchCase: false }).click()
    cy.waitForStreamlit()
    
    // Try to connect without filling form
    cy.contains('button', 'Connect', { matchCase: false }).click()
    
    // Should show error or validation message
    cy.get('body').should('contain.text', 'missing').or('contain.text', 'required')
  })
})

