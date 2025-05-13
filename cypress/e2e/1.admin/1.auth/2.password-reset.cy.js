describe("Check password reset", () => {
  it("Check forgot password", () => {
    cy.visit("/");
    cy.get("a").contains("Forgot password?").click();
    cy.get("input[type=email]").type("invalid@example.com");
    cy.get("[type=submit]").click();
    cy.contains("Password reset instructions have been sent");
  });
});
