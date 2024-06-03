describe("Check import focal points", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Import legacy contacts task",
      searchValue: "4a0665ef-d79f-444e-84d9-35f26fbef7fc",
    });
  });
  it("Check import legacy contacts", () => {
    cy.loginAdmin();
    cy.addModel("Import legacy contacts task", {
      json_file: "fixtures/test/files/legacy-contacts.json",
    });
    cy.get("#result_list tbody tr:first-of-type .field-status_display").contains("SUCCESS");
    cy.get("#result_list tbody tr:first-of-type th a").click();
    cy.contains("Contacts created=2");

    // Check some of the imported fields
    cy.performSearch({
      modelName: "Contacts",
      searchValue: "jane1.legacy-test@example.com",
      filters: { groups__id__exact: "Legacy contacts" },
    });
    cy.get("#result_list tbody tr:first-of-type th a").click();
    cy.contains("Ms. Jane Doe");
    cy.contains("Guyana (GY)");
    cy.get('[name=emails][value="jane1.legacy-test@example.com"]');
    cy.get('[name=emails][value="jane2.legacy-test@example.com"]');
    cy.get("[name=designation]").should("have.value", "Officer");

    // Remove imported data
    cy.triggerAction({
      modelName: "Contacts",
      action: "Delete selected contacts",
      searchValue: "legacy-test@example.com",
      filters: { groups__id__exact: "Legacy contacts" },
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
  });
});
