describe("Check user permissions", () => {
  it("Check emails access", () => {
    cy.loginEmails();
    cy.checkAccess({
      core: {
        contact: { view: true },
        contactgroup: { view: true },
      },
      emails: {
        email: { add: true, view: true },
        emailtemplate: true,
        sendemailtask: { view: true },
      },
      events: {
        event: { view: true },
      },
    });
  });
});
