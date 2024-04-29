describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Contacts", nameField: "last_name" });
  });
  it("Check merge contacts", () => {
    cy.loginEdit();
    cy.createContactGroup(2).then((group) => {
      cy.triggerAction("Contacts", { groups__id__exact: group.name, action: "Merge selected contacts" });
      cy.checkSearch({ modelName: "Resolve conflicts", searchValue: group.contacts[0].last_name });
      cy.get("input[value=Save]").click();
      cy.contains("changed successfully");
      cy.checkNotFound({ modelName: "Resolve conflicts", searchValue: group.contacts[0].last_name });
      cy.deleteContactGroup(group);
    });
  });
});
