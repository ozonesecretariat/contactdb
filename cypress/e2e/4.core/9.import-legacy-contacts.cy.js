describe("Check import focal points", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Import legacy contacts task",
      searchValue: "4a0665ef-d79f-444e-84d9-35f26fbef7fc",
    });
  });
});
