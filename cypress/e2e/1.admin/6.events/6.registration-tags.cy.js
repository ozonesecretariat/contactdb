describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration tags" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["credential", "online", "viewer", "visa"],
      filePattern: "RegistrationTag",
      modelName: "Registration tags",
    });
  });
});
