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
        importcontactphotostask: { view: true },
        importfocalpointstask: { add: true, view: true },
        importlegacycontactstask: { add: true, view: true },
        organization: true,
        organizationtype: true,
        possibleduplicatecontact: { view: true },
        possibleduplicateorganization: { view: true },
        region: true,
        resolveconflict: { view: true },
        subregion: true,
      },
      emails: {
        email: { add: true, view: true },
        emailtemplate: true,
        invitationemail: { add: true, view: true },
        sendemailtask: { view: true },
      },
      events: {
        event: true,
        eventgroup: true,
        eventinvitation: true,
        loadeventsfromkronostask: { add: true, view: true },
        loadorganizationsfromkronostask: { view: true },
        loadparticipantsfromkronostask: { view: true },
        registration: true,
        registrationrole: true,
        registrationstatus: true,
        registrationtag: true,
      },
    });
  });
});
