describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch("Contact groups", "dream team", "The Dream Team Connection");
  });
  it("Check add and delete", () => {
    cy.loginEdit();
    cy.checkAdd("Contact groups");
  });
});
