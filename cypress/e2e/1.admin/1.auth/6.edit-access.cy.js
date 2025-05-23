describe("Check user permissions", () => {
  it("Check edit access", () => {
    cy.loginEdit();
    cy.checkAccess({
      core: {
        contact: true,
        contactgroup: true,
        country: true,
        organization: true,
        organizationtype: true,
        possibleduplicate: { view: true },
        resolveconflict: { view: true },
      },
      events: {
        event: true,
        eventgroup: true,
        eventinvitation: true,
        registration: true,
        registrationrole: true,
        registrationstatus: true,
        registrationtag: true,
      },
    });
  });
});
