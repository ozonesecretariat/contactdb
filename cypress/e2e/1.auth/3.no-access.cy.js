describe("Check user permissions", () => {
  it("Check no access", () => {
    cy.loginNoAccess();
    cy.checkAccess({});
  });
});
