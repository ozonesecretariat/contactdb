describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch("Organizations", "exoplanetary", "Exoplanetary Colonization Authority");
  });
  it("Check add and delete", () => {
    cy.loginEdit();
    cy.checkAdd("Organizations", "name", { organization_type: "OTHER" });
  });
});
