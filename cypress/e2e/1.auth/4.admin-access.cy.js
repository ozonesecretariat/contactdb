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
        config: { view: true, change: true },
      },
      core: {
        contactgroup: true,
        contact: true,
        country: true,
        importfocalpointstask: { add: true, view: true },
        organizationtype: true,
        organization: true,
        possibleduplicate: { view: true },
        resolveconflict: { view: true },
      },
      emails: {
        emailtemplate: true,
        email: { add: true, view: true },
        sendemailtask: { view: true },
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
