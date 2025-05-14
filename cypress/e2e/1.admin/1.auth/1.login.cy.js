describe("Check login", () => {
  it("Check login admin", () => {
    cy.loginAdmin();
    cy.get("body").contains("Welcome, admin@example.com");
    cy.get("button").contains("Log out").click();
    cy.contains("Login");
  });
  it("Check bad login", () => {
    cy.visit("/");
    cy.login("inactive@example.com", "inactive", false);
    cy.contains("Please enter a correct email and password.");
    cy.login("admin@example.com", "badmin", false);
    cy.contains("Please enter a correct email and password.");
    cy.login("badmin@example.com", "admin", false);
    cy.contains("Please enter a correct email and password.");
  });
  it("Check forgot password", () => {
    cy.visit("/");
    cy.get("a").contains("Forgot password?").click();
    cy.get("input[type=email]").type("invalid@example.com");
    cy.get("[type=submit]").click();
    cy.contains("Password reset instructions have been sent");
  });
});
