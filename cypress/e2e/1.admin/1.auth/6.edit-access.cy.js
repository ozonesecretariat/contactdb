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
        possibleduplicatecontact: { view: true },
        possibleduplicateorganization: { view: true },
        resolveconflict: { view: true },
      },
      events: {
        event: true,
        eventgroup: true,
        eventinvitation: true,
        prioritypass: { change: true, view: true },
        registration: true,
        registrationrole: true,
        registrationtag: true,
      },
    });
  });
});
