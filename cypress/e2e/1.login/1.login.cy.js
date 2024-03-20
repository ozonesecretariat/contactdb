describe("Check login", () => {
  it("Check login admin", () => {
    cy.login();
    cy.get("a").contains("Hello, admin@example.com");
    cy.get("button").contains("Log Out").click();
    cy.get("h1").contains("Login");
  });
});
