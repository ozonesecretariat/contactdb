describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch("Organization types", "expert", "ACC-EXPERT");
  });
  it("Check add and delete", () => {
    cy.loginEdit();
    cy.checkAdd("Organization types");
  });
});
