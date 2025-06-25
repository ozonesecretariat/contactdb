describe("Check user permissions", () => {
  it("Check kronos access", () => {
    cy.loginKronos();
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
        loadeventsfromkronostask: { add: true, view: true },
        loadorganizationsfromkronostask: { view: true },
        loadparticipantsfromkronostask: { view: true },
        registration: true,
        registrationrole: true,
        registrationtag: true,
      },
    });
  });
});
