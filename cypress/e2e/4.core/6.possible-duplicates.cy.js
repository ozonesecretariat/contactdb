describe("Check possible duplicates", () => {
  it("Check search", () => {
    cy.loginEdit();
    cy.checkSearch({
      modelName: "Possible duplicates",
      searchValue: "elara@example.com",
      expectedValue: "Email: elara@example.com",
    });
  });
  it("Check dismiss", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { email_ccs: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
        expectedValue: "duplicate-check@example.org",
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Dismiss").click();
      cy.checkNotFound({ modelName: "Possible duplicates", searchValue: group.contacts[0].last_name });
      cy.checkSearch({
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
        expectedValue: "duplicate-check@example.org",
        filters: {
          is_dismissed: "Yes",
        },
      });

      cy.deleteContactGroup(group);
    });
  });
  it("Check merge", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { email_ccs: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
        expectedValue: "duplicate-check@example.org",
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Merge").click();
      cy.checkNotFound({ modelName: "Possible duplicates", searchValue: group.contacts[0].last_name });
      cy.deleteContactGroup(group);
    });
  });
});