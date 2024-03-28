describe("Check login", () => {
  it("Check login admin", () => {
    cy.login();
    cy.get("body").contains("Welcome, admin@example.com");
    cy.get("button").contains("Log out").click();
    cy.get("h1").contains("Enter credentials");
  });
});
