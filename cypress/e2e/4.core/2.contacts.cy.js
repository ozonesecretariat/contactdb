describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch("Contacts", "eris-nyx", "Eris-Nyx");
  });
  it("Check add and delete", () => {
    cy.loginAdmin();
    cy.checkAdd("Contacts", "last_name");
  });
});
