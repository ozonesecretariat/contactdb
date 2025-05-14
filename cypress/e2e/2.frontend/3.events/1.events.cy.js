describe("Check events page", () => {
  it("Check events page", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.contains("1-15 of 20");
  });
  it("Check search events", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.get("[role=search]").type("expo");
    cy.contains("1-2 of 2");
  });
});
