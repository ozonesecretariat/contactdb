describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.checkModelAdmin({
        extraFields: {
          contact: contact.last_name,
          date_0: "2024-04-18",
          date_1: "00:00:00",
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
