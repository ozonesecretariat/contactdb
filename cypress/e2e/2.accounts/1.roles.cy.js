describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch("Roles", "kronos", "Load from Kronos");
  });
  it("Check add and delete", () => {
    cy.loginAdmin();
    cy.checkAdd("Roles");
  });
});
