describe("Check login", () => {
  it("Check login admin", () => {
    cy.loginAdmin();
    cy.get("body").contains("Welcome, admin@example.com");
    cy.get("button").contains("Log out").click();
    cy.get("h1").contains("Enter credentials");
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
    cy.get("a").contains("Forgotten your password").click();
    cy.get("input[type=email]").type("invalid@example.com");
    cy.get("input[type=submit]").click();
    cy.get("h1").contains("Password reset sent");
  });
});
