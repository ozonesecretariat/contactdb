describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      expectedValue: "Test placeholder email",
      modelName: "Send email tasks",
      searchValue: "placeholder atlas drake",
    });

    cy.task("cleanDownloadsFolder");
    cy.get("a").contains("Download").click();
    cy.checkFile({
      expected: [
        "Test placeholder email",
        "Dear Atlas Drake",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit",
        "Kind Regards",
      ],
      filePattern: "75bf59cd-bede-4149-ba4b-7bd1a6f90312.eml",
    });
  });
  it("Check contact link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Send email tasks",
      searchValue: "placeholder atlas drake",
    });
    cy.get("a").contains("Atlas Drake (Deep Space Exploration Agency, Tuvalu)").click();
    cy.contains("Change contact");
  });
  it("Check filter Any contact", () => {
    cy.loginAdmin();
    cy.performSearch({
      filters: {
        any_contact: "Rigel Rift",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("1 result");

    cy.performSearch({
      filters: {
        any_contact: "🐉",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("46 result");

    cy.performSearch({
      filters: {
        any_contact: "Ezra Spectrum",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("46 result");
  });
  it("Check filter To contact", () => {
    cy.loginAdmin();
    cy.performSearch({
      filters: {
        contact: "Rigel Rift",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("1 result");
  });
  it("Check filter Cc contact", () => {
    cy.loginAdmin();
    cy.performSearch({
      filters: {
        cc_contacts: "🐉",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("46 results");
  });
  it("Check filter Bcc contact", () => {
    cy.loginAdmin();
    cy.performSearch({
      filters: {
        bcc_contacts: "Ezra Spectrum",
        email: "Test email with Cc and Bcc",
      },
      modelName: "Send email tasks",
    });
    cy.contains("46 results");
  });
});
