describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Load events from kronos task",
      searchValue: "569b6a62-ef1f-4953-a60f-62fde626548f",
    });
  });
});
