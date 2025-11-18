describe('Homepage Tests', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.waitForStreamlit()
  })

  it('should load the homepage', () => {
    cy.get('body').should('be.visible')
    cy.contains('Medad Automation Tools', { matchCase: false }).should('be.visible')
  })

  it('should display login form when not authenticated', () => {
    // Check if login form elements are present
    cy.get('input[type="text"], input[type="password"]').should('exist')
    cy.contains('button', 'Login', { matchCase: false }).should('exist')
  })

  it('should show error for invalid credentials', () => {
    cy.get('input[type="text"], input[name*="username"]').first().type('invalid_user')
    cy.get('input[type="password"]').first().type('invalid_password')
    cy.contains('button', 'Login', { matchCase: false }).click()
    
    // Wait for error message
    cy.contains('incorrect', { matchCase: false, timeout: 5000 }).should('be.visible')
  })
})

