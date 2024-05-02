describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Log entries",
      searchValue: "romania",
      expectedValue: "Romania (RO)",
    });
    cy.get("a").contains("History").click();
    cy.contains("1 result");
    cy.get("#result_list tbody th").click();
    cy.contains("View log entry");
    cy.contains("Created Romania (RO)");
  });
});
