describe("Check nominations page", () => {
  it("Check nominations page group and gov invitation token", () => {
    cy.loginAdmin(false);
    cy.visit("/token/0a8a390b-c5a5-4ba0-a06e-a78097382bb4/nominations");
    cy.contains("1-7 of 7");
    cy.get("[role=search]").type("authority");
    cy.contains("1-3 of 3");
  });
  it("Check nominations no auth", () => {
    cy.visit("/token/0a8a390b-c5a5-4ba0-a06e-a78097382bb4/nominations");
    cy.contains("1-7 of 7");
    cy.get("[role=search]").type("authority");
    cy.contains("1-3 of 3");
  });
  it("Check nominations no token", () => {
    cy.visit("/token/xxx-xxx-xxx-xxx-xxxx/nominations");
    cy.contains("No data available");
  });
});
