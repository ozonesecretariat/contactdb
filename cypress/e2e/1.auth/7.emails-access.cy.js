describe("Check user permissions", () => {
  it("Check emails access", () => {
    cy.loginEmails();
    cy.checkAccess({
      core: {
        contactgroup: { view: true },
        contact: { view: true },
      },
      emails: {
        emailtemplate: true,
        email: { add: true, view: true },
        sendemailtask: { view: true },
      },
      events: {
        event: { view: true },
      },
    });
  });
});
