describe("Check constance", () => {
  it("Check view config", () => {
    cy.loginAdmin();
    cy.get("a").contains("Config").click();
    cy.get("h1").contains("Constance");
    cy.contains("REQUIRE_2FA");
    cy.contains("APP_TITLE");
    cy.contains("WELCOME_MESSAGE");
  });
});
