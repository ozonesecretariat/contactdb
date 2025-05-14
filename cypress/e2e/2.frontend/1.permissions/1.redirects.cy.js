describe("Check redirects", () => {
  it("Check redirect after login", () => {
    cy.visit("/account/settings");
    cy.contains("Must be logged in to view this page.");
    cy.get("input[autocomplete=email]").type("admin@example.com");
    cy.get("input[autocomplete=current-password]").type("admin");
    cy.get("[type=submit]:not([hidden])").click();
    // check that we redirect back to the account settings page
    cy.url().should("include", "/account/settings");
    cy.checkNavActive("Account settings");
  });
  it("Check unsafe redirect after login", () => {
    cy.visit("/auth/login?next=https://example.com");
    cy.get("input[autocomplete=email]").type("admin@example.com");
    cy.get("input[autocomplete=current-password]").type("admin");
    cy.get("[type=submit]:not([hidden])").click();
    // check that we redirect back to the home page
    cy.checkNavActive("Home");
  });
  it("Check access anon only page while logged in", () => {
    cy.loginAdmin(false);
    cy.visit("/auth/login");
    // check that we redirect back to the home page
    cy.checkNavActive("Home");
  });
  it("Check access page without permissions", () => {
    cy.loginNoAccess(false);
    cy.visit("/events");
    // check that we redirect back to the home page
    cy.checkNavActive("Home");
    cy.contains("Your account does not have the required permissions");
  });
});
