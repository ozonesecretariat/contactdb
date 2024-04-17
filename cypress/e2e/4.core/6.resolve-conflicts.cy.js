describe("Check resolve conflicts", () => {
  it("Check search conflicts", () => {
    cy.loginEdit();
    cy.checkSearch("Resolve conflicts", "ireland", "Mr. Aurora");
  });
});
