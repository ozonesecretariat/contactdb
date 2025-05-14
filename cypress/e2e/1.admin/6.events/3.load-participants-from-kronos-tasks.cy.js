describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      expectedValue: "Mythos Masquerade Ball",
      modelName: "Load participants from kronos task",
      searchValue: "masquerade",
    });
  });
});
