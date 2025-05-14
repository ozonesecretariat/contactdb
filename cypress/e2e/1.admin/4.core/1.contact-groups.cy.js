describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Contact groups" });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Focal point", "NFP", "FPLS", "Legacy contacts"],
      filePattern: "ContactGroup",
      filters: {
        predefined__exact: "Yes",
      },
      modelName: "Contact groups",
    });
  });
  it("Check contacts link", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Contact groups",
      searchValue: "syndicate",
    });
    cy.get("a").contains("10 contacts").click();
    cy.contains("Select contact");
    cy.contains("10 results");
  });
  it("Check send email to groups", () => {
    cy.loginAdmin();
    cy.triggerAction({
      action: "Send email to selected groups",
      filters: {
        predefined__exact: "Yes",
      },
      modelName: "Contact groups",
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("Focal point");
    cy.get(".select2-selection__choice").contains("NFP");
    cy.get(".select2-selection__choice").contains("FPLS");
    // Should not be included as there no contacts in the groups in the test db.
    cy.get(".select2-selection__choice").contains("Legacy contacts").should("not.exist");
  });
});
