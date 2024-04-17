describe("Check password reset", () => {
  it("Check forgot password", () => {
    cy.visit("/");
    cy.get("a").contains("Forgotten your password").click();
    cy.get("input[type=email]").type("invalid@example.com");
    cy.get("input[type=submit]").click();
    cy.get("h1").contains("Password reset sent");
  });
});
