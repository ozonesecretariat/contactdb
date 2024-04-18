describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Organizations", extraFields: { organization_type: "OTHER" } });
  });
});
