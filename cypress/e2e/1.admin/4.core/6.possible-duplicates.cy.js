describe("Check possible duplicates", () => {
  it("Check search", () => {
    cy.loginEdit();
    cy.checkSearch({
      expectedValue: "Email: elara@example.com",
      modelName: "Possible duplicates",
      searchValue: "elara@example.com",
    });
    cy.contains("Élàra Vãngüard");
  });
  it("Check dismiss", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { email_ccs: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Dismiss").click();
      cy.checkNotFound({ modelName: "Possible duplicates", searchValue: group.contacts[0].last_name });
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        filters: {
          is_dismissed: "Yes",
        },
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
      });

      cy.deleteContactGroup(group);
    });
  });
  it("Check dismiss bulk", () => {
    cy.loginEdit();

    cy.createContactGroup(2, { email_ccs: "duplicate-check@example.org" }).then((group) => {
      cy.triggerAction({
        action: "Dismiss selected duplicates",
        modelName: "Possible duplicates",
        searchValue: "duplicate-check@example.org",
      });
      cy.checkNotFound({ modelName: "Possible duplicates", searchValue: group.contacts[0].last_name });
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        filters: {
          is_dismissed: "Yes",
        },
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
      });
      cy.deleteContactGroup(group);
    });
  });
  it("Check merge", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { email_ccs: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        modelName: "Possible duplicates",
        searchValue: group.contacts[0].last_name,
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Merge").click();
      cy.checkNotFound({ modelName: "Possible duplicates", searchValue: group.contacts[0].last_name });
      cy.deleteContactGroup(group);
    });
  });
});
