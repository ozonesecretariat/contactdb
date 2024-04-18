describe("Check", () => {
  it("Check model admin", () => {
    cy.loginAdmin();
    cy.checkModelAdmin({ modelName: "Roles" });
  });
});
