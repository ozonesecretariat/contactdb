describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch("Countries", "romania", "RO");
  });
});
