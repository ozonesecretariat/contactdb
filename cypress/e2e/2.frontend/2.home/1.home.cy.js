describe("Check home page", () => {
  it("Check home page", () => {
    cy.loginAdmin(false);
    cy.checkNavActive("Home");
  });
});
