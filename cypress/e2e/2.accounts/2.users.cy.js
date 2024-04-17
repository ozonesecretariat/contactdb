describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch("Users", "admin", "admin@example.com");
  });
  it("Check add and delete", () => {
    cy.loginAdmin();
    cy.checkAdd("Users", "email", {}, "@example.org");
  });
});
