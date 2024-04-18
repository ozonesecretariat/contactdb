describe("Check", () => {
  it("Check model admin", () => {
    cy.loginAdmin();
    cy.checkModelAdmin({ modelName: "Users", nameField: "email", suffix: "@example.org" });
  });
});
