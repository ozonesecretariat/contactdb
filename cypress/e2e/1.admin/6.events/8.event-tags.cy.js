describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      modelName: "Event tags",
    });
  });
});
