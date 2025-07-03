describe("Check scan pass", () => {
  it("Go to pass via url", () => {
    cy.loginAdmin(false);
    cy.visit("/scan-pass?code=69EFWLUG49");
    cy.contains("Luna-Nova Vortex");
    cy.contains("Psychedelic Dreamscape Art Fair");
    cy.contains("Quantum Quest: A Science Adventure Symposium");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
    cy.contains("Accredited");
    cy.contains("Nominated");
  });
  it("Go to pass via search", () => {
    cy.loginAdmin(false);
    cy.contains("Scan Pass").click();
    cy.contains("Search for pass").click();
    cy.get("[role=search]").type("serenade drake astrid{enter}");
    cy.contains("Ms. Astrid-Drake Spectrum | Cosmic Nexus Intelligence Agency").click();
    cy.contains("astrid-drake@example.com");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
    cy.contains("Ms. Astrid-Drake Spectrum");
    cy.contains("Accredited");
  });
  it("Check register", () => {
    cy.loginEdit();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.addModel("Registrations", {
        contact: contact.last_name,
        event: "Yoga Experience",
        role: "Alternate Head",
        status: "Accredited",
      });
      cy.checkSearch({
        modelName: "Registrations",
        searchValue: contact.last_name,
      });
      cy.get(".field-priority_pass a").click();
      cy.get("a").contains("Scan").goToHref();
      cy.contains(contact.last_name);
      cy.contains("Register").click();
      cy.contains("Registration status updated.");
      cy.contains("Registered");
      cy.contains("Admin").click();
      cy.deleteContactGroup(group);
    });
  });
  it("Check revoke", () => {
    cy.loginEdit();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.addModel("Registrations", {
        contact: contact.last_name,
        event: "Yoga Experience",
        role: "Alternate Head",
        status: "Accredited",
      });
      cy.checkSearch({
        modelName: "Registrations",
        searchValue: contact.last_name,
      });
      cy.get(".field-priority_pass a").click();
      cy.get("a").contains("Scan").goToHref();
      cy.contains(contact.last_name);
      cy.contains("Revoke").click();
      cy.contains("Registration status updated.");
      cy.contains("Revoked");
      cy.contains("Admin").click();
      cy.deleteContactGroup(group);
    });
  });
});
