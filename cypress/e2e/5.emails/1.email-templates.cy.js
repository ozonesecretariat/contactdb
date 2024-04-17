describe("Check", () => {
  it("Check search", () => {
    cy.loginEmails();
    cy.checkSearch("Email templates", "full name", "Test placeholders");
  });
  it("Check add and delete", () => {
    cy.loginEmails();
    cy.checkAdd("Email templates", "title", {
      description: "test template description",
      content: "test template content",
    });
  });
});
