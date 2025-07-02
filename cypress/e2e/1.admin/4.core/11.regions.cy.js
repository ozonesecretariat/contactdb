describe("Check", () => {
  it("Check region model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Region", nameField: "Name" });
  });
  it("Check subregion model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Subregion", nameField: "Name" });
  });
});
