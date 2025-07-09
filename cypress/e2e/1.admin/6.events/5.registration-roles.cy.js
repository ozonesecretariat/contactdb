describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration roles" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Delegate", "Unofficial Delegate"],
      filePattern: "RegistrationRole",
      modelName: "Registration roles",
      searchValue: "delegate",
    });
  });
});
