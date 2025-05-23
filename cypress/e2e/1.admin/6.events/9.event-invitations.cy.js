describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      extraFields: {
        country: "Uruguay",
        event: "Yoga Experience",
      },
      modelName: "Event invitations",
      nameField: null,
      searchValue: "Yoga",
    });
  });
});
