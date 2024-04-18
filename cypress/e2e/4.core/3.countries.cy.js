describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch({ modelName: "Countries", searchValue: "romania", expectedValue: "RO" });
  });
});
