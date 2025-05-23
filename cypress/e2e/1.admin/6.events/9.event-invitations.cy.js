describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      extraFields: {
        event: "Yoga Experience",
        country: "Uruguay",
      },
      modelName: "Event invitations",
      nameField: null,
      searchValue: "Yoga",
    });
  });
});
