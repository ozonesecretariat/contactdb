describe("Check", () => {
  it("Check search", () => {
    cy.loginView();
    cy.checkSearch({ modelName: "Countries", searchValue: "romania", expectedValue: "RO" });
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
