describe("Check possible duplicate contacts", () => {
  it("Check search", () => {
    cy.loginEdit();
    cy.checkSearch({
      expectedValue: "Email: elara@example.com",
      modelName: "Possible duplicate contacts",
      searchValue: "elara@example.com",
    });
    cy.contains("Élàra Vãngüard");
  });
  it("Check dismiss", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { emails: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        modelName: "Possible duplicate contacts",
        searchValue: group.contacts[0].last_name,
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Dismiss").click();
      cy.checkNotFound({ modelName: "Possible duplicate contacts", searchValue: group.contacts[0].last_name });
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        filters: {
          is_dismissed: "Yes",
        },
        modelName: "Possible duplicate contacts",
        searchValue: group.contacts[0].last_name,
      });

      cy.deleteContactGroup(group);
    });
  });
  it("Check dismiss bulk", () => {
    cy.loginEdit();

    cy.createContactGroup(2, { emails: "duplicate-check@example.org" }).then((group) => {
      cy.triggerAction({
        action: "Dismiss selected duplicates",
        modelName: "Possible duplicate contacts",
        searchValue: "duplicate-check@example.org",
      });
      cy.checkNotFound({ modelName: "Possible duplicate contacts", searchValue: group.contacts[0].last_name });
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        filters: {
          is_dismissed: "Yes",
        },
        modelName: "Possible duplicate contacts",
        searchValue: group.contacts[0].last_name,
      });
      cy.deleteContactGroup(group);
    });
  });
  it("Check merge", () => {
    cy.loginEdit();
    cy.createContactGroup(2, { emails: "duplicate-check@example.org" }).then((group) => {
      cy.checkSearch({
        expectedValue: "duplicate-check@example.org",
        modelName: "Possible duplicate contacts",
        searchValue: group.contacts[0].last_name,
      });
      cy.contains(group.contacts[0].last_name);
      cy.contains(group.contacts[1].last_name);
      cy.get("a").contains("Merge").click();
      cy.checkNotFound({ modelName: "Possible duplicate contacts", searchValue: group.contacts[0].last_name });
      cy.deleteContactGroup(group);
    });
  });
});
