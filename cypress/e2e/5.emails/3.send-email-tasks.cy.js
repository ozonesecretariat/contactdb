describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Send email tasks",
      searchValue: "placeholder atlas drake",
      expectedValue: "Test placeholder email",
    });
  });
});
