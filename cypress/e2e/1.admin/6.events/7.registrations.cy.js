describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.checkModelAdmin({
        extraFields: {
          contact: contact.last_name,
          event: "Yoga Experience",
          role: "Alternate Head",
          status: "Registered",
        },
        filters: {
          event: "Yoga Experience",
        },
        modelName: "Registrations",
        nameField: null,
        searchValue: contact.last_name,
      });
      cy.deleteContactGroup(group);
    });
  });
  it("Check sending email", () => {
    cy.loginAdmin();
    cy.triggerAction({
      action: "Send email to selected contacts",
      modelName: "Registrations",
      searchValue: "kai nova",
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("MP Kai Nova");
    cy.get(".select2-selection__choice").contains("Mr. Kai-Nova Nova");
  });
});
