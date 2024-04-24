describe("Check user permissions", () => {
  it("Check kronos access", () => {
    cy.loginKronos();
    cy.checkAccess({
      core: {
        contactgroup: true,
        contact: true,
        country: true,
        organizationtype: true,
        organization: true,
        possibleduplicate: { view: true },
        resolveconflict: { view: true },
      },
      events: {
        event: true,
        loadeventsfromkronostask: { add: true, view: true },
        loadparticipantsfromkronostask: { view: true },
        registrationrole: true,
        registrationstatus: true,
        registrationtag: true,
        registration: true,
      },
    });
  });
});
