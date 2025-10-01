describe("Check events page", () => {
  it("Check events page", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.checkNavActive("Events");
    cy.contains("1-3 of 3");
    // Check default sort order
    cy.get("tbody tr:first-of-type").contains("Spectrum Symposium: Colorful Conference on Creativity");
  });
  it("Check search events", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.checkNavActive("Events");
    cy.get("[role=search]").type("music");
    cy.contains("1-1 of 1");
  });
  it("Check link to dashboard", () => {
    cy.loginAdmin(false);
    cy.checkNav("Events").click();
    cy.checkNavActive("Events");
    cy.get("tr").contains("Stéllâr Sérènade Müsïc Fêstivàl").click();
    cy.checkNavActive("Dashboard");
  });
});
