describe("Check menu items", () => {
  it("Check super user", () => {
    cy.loginAdmin(false);
    cy.checkNav("Admin");
    cy.checkNav("Events");
  });
  it("Check view only user", () => {
    cy.loginView(false);
    cy.checkNav("Admin");
    cy.checkNav("Events");
  });
  it("Check non staff user", () => {
    cy.loginNonStaff(false);
    cy.checkNav("Admin").should("not.exist");
    cy.checkNav("Events");
  });
  it("Check non staff user view", () => {
    cy.loginNonStaffView(false);
    cy.checkNav("Admin").should("not.exist");
    cy.checkNav("Events");
  });
  it("Check non staff user no access", () => {
    cy.loginNonStaffNoAccess(false);
    cy.checkNav("Admin").should("not.exist");
    cy.checkNav("Events").should("not.exist");
  });
});
