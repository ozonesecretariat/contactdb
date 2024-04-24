describe("Check resolve conflicts", () => {
  it("Check search conflicts", () => {
    cy.loginEdit();
    cy.checkSearch({ modelName: "Resolve conflicts", searchValue: "ireland", expectedValue: "Mr. Aurora" });
  });
});
