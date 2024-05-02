describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration statuses" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Registration statuses",
      filePattern: "RegistrationStatus",
      expected: ["Accredited", "Nominated", "Registered"],
    });
  });
});
