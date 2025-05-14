describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      extraFields: {
        content: "test template content",
        description: "test template description",
      },
      modelName: "Email templates",
      nameField: "title",
    });
  });
});
