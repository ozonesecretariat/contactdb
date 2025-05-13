describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Email templates",
      nameField: "title",
      extraFields: {
        description: "test template description",
        content: "test template content",
      },
    });
  });
});
