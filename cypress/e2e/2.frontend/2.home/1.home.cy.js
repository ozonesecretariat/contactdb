describe("Check home page", () => {
  it("Check home page admin", () => {
    cy.loginAdmin(false);
    cy.checkNavActive("Events");
  });
  it("Check home page security", () => {
    cy.loginSecurity(false);
    cy.checkNavActive("Scan Pass");
  });
  it("Check home page support", () => {
    cy.loginSupport(false);
    cy.checkNavActive("Scan Pass");
  });
  it("Check home page DSA", () => {
    cy.loginDSA(false);
    cy.checkNavActive("Delegates");
  });
  it("Check home page no access", () => {
    cy.loginNonStaffNoAccess(false);
    cy.contains("Welcome, test-non-staff-no-access@example.com");
  });
});
