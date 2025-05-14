describe("Check user permissions", () => {
  it("Check admin access", () => {
    cy.loginAdmin();
    cy.checkAccess({
      accounts: {
        role: true,
        user: true,
      },
      auditlog: {
        logentry: { view: true },
      },
      constance: {
        config: { change: true, view: true },
      },
      core: {
        contact: true,
        contactgroup: true,
        country: true,
        importfocalpointstask: { add: true, view: true },
        importlegacycontactstask: { add: true, view: true },
        organization: true,
        organizationtype: true,
        possibleduplicate: { view: true },
        resolveconflict: { view: true },
      },
      emails: {
        email: { add: true, view: true },
        emailtemplate: true,
        sendemailtask: { view: true },
      },
      events: {
        event: true,
        loadeventsfromkronostask: { add: true, view: true },
        loadparticipantsfromkronostask: { view: true },
        registration: true,
        registrationrole: true,
        registrationstatus: true,
        registrationtag: true,
      },
    });
  });
});
