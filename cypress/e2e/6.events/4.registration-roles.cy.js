describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Registration roles" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Registration roles",
      searchValue: "delegate",
      filePattern: "RegistrationRole",
      expected: ["Delegate", "Unofficial Delegate"],
    });
  });
});
