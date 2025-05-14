describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration statuses" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Accredited", "Nominated", "Registered"],
      filePattern: "RegistrationStatus",
      modelName: "Registration statuses",
    });
  });
});
