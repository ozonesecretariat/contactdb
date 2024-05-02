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
  it("Check success link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("19 emails").click();
    cy.contains("Select send email task");
    cy.contains("MP Nyx Spectrum");
    cy.contains("19 results");
  });
  it("Check failure link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("5 emails").click();
    cy.contains("Select send email task");
    cy.contains("Ms. Astrid-Cassius Galactic");
    cy.contains("5 results");
  });
  it("Check pending link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("6 emails").click();
    cy.contains("Select send email task");
    cy.contains("Mr. Rigel Zephyr");
    cy.contains("6 results");
  });
});
