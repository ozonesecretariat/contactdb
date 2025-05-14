describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Organization types", nameField: "acronym" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Interpreters", "Industry"],
      filePattern: "OrganizationType",
      modelName: "Organization types",
      searchValue: "in",
    });
  });
});
