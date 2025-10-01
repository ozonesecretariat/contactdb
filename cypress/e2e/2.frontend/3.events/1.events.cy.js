describe("Check events page", () => {
  it("Check events page", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.contains("1-3 of 3");
  });
  it("Check search events", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.get("[role=search]").type("music");
    cy.contains("1-1 of 1");
  });
});
