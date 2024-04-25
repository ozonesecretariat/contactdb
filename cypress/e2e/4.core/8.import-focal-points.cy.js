describe("Check import focal points", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Import focal points task",
      searchValue: "47aae0ca-5a52-4db1-b1c3-8b35ad615c6d",
    });
  });
});
