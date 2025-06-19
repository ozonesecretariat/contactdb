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
});
