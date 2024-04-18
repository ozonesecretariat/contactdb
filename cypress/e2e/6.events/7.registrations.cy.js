describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      modelName: "Registrations",
      nameField: null,
      extraFields: {
        contact: "Rhea-Drake Cosmos",
        event: "Yoga Experience",
        status: "Registered",
        role: "Alternate Head",
        date_0: "2024-04-18",
        date_1: "00:00:00",
      },
      searchValue: "Rhea-Drake",
      filters: {
        contact: "Rhea-Drake Cosmos",
        event: "Yoga Experience",
      },
    });
  });
});
