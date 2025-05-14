describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch({ expectedValue: "Türkiye", modelName: "Countries", searchValue: "turkiye" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Central African Republic", "South Africa"],
      filePattern: "Country",
      modelName: "Countries",
      searchValue: "Africa",
    });
  });
});
