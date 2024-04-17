describe("Check user permissions", () => {
  it("Check view access", () => {
    cy.loginView();
    cy.checkAccess({
      core: {
        contactgroup: { view: true },
        contact: { view: true },
        country: { view: true },
        organizationtype: { view: true },
        organization: { view: true },
      },
      events: {
        event: { view: true },
        registrationrole: { view: true },
        registrationstatus: { view: true },
        registrationtag: { view: true },
        registration: { view: true },
      },
    });
  });
});
