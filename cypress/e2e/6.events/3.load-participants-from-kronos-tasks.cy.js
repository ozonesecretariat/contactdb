describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Load participants from kronos task",
      searchValue: "masquerade",
      expectedValue: "Mythos Masquerade Ball",
    });
  });
});
