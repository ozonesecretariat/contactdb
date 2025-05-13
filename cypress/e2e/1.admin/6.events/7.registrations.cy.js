describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.checkModelAdmin({
        modelName: "Registrations",
        nameField: null,
        extraFields: {
          contact: contact.last_name,
          event: "Yoga Experience",
          status: "Registered",
          role: "Alternate Head",
          date_0: "2024-04-18",
          date_1: "00:00:00",
        },
        searchValue: contact.last_name,
        filters: {
          event: "Yoga Experience",
        },
      });
      cy.deleteContactGroup(group);
    });
  });
});
