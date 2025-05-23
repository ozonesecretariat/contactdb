describe("Check user permissions", () => {
  it("Check view access", () => {
    cy.loginView();
    cy.checkAccess({
      core: {
        contact: { view: true },
        contactgroup: { view: true },
        country: { view: true },
        organization: { view: true },
        organizationtype: { view: true },
      },
      events: {
        event: { view: true },
        eventgroup: { view: true },
        eventinvitation: { view: true },
        registration: { view: true },
        registrationrole: { view: true },
        registrationstatus: { view: true },
        registrationtag: { view: true },
      },
    });
  });
});
