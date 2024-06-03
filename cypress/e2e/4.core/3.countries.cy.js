describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch({ modelName: "Countries", searchValue: "turkiye", expectedValue: "Türkiye" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Countries",
      searchValue: "Africa",
      filePattern: "Country",
      expected: ["Central African Republic", "South Africa"],
    });
  });
});
