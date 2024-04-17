describe("Check user permissions", () => {
  it("Check edit access", () => {
    cy.loginEdit();
    cy.checkAccess({
      core: {
        contactgroup: true,
        contact: true,
        country: true,
        organizationtype: true,
        organization: true,
        resolveconflict: { view: true },
      },
      events: {
        event: true,
        registrationrole: true,
        registrationstatus: true,
        registrationtag: true,
        registration: true,
      },
    });
  });
});
