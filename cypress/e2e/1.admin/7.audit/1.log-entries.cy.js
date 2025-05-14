describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      expectedValue: "Romania (RO)",
      modelName: "Log entries",
      searchValue: "romania",
    });
    cy.get("a").contains("History").click();
    cy.contains("1 result");
    cy.get("#result_list tbody th").click();
    cy.contains("View log entry");
    cy.contains("Created Romania (RO)");
  });
});
