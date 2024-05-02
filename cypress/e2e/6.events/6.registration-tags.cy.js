describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration tags" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Registration tags",
      filePattern: "RegistrationTag",
      expected: ["credential", "online", "viewer", "visa"],
    });
  });
});
