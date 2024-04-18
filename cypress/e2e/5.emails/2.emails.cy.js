describe("Check", () => {
  it("Check send", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "Aria-Eclipse Titan",
        groups: "Literary Legends League",
        events: "Zenith Zen: Skyline Yoga Experience",
        content: "Test sending email",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });
  });
});
