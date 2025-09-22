describe("Check scan pass", () => {
  it("Go to pass via url", () => {
    cy.loginAdmin(false);
    cy.visit("/scan-pass?code=69EFWLUG49");
    cy.contains("Luna-Nova Vortex");
    cy.contains("Intergalactic Defense Coalition");
    cy.contains("Spain");
    cy.contains("Psychedelic Dreamscape Art Fair");
    cy.contains("Quantum Quest: A Science Adventure Symposium");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
    cy.contains("Accredited");
    cy.contains("Nominated");
    cy.contains("Take photo");
    // Can't print badge because participant isn't registered yet
    cy.should("not.contain", "Print badge");
  });
  it("Check support staff view", () => {
    cy.loginSupport(false);
    cy.visit("/scan-pass?code=T6UQZRYW0S");
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("lyra-pulse@example.com");
    cy.contains("Registered 11 Jul 2020 to 7 Jun 2023");
    cy.contains("Psychedelic Dreamscape Art Fair");
    cy.contains("Quantum Quest: A Science Adventure Symposium");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
    cy.contains("Accredited");
    cy.contains("Registered");
    cy.contains("Print badge");
    cy.should("not.contain", "Take photo");
  });
  it("Check security staff view", () => {
    cy.loginSecurity(false);
    cy.visit("/scan-pass?code=T6UQZRYW0S");
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("Registered 11 Jul 2020 to 7 Jun 2023");
    cy.should("not.contain", "lyra-pulse@example.com");
    cy.should("not.contain", "Psychedelic Dreamscape Art Fair");
    cy.should("not.contain", "Quantum Quest: A Science Adventure Symposium");
    cy.should("not.contain", "Stéllâr Sérènade Müsïc Fêstivàl");
    cy.should("not.contain", "Print badge");
    cy.should("not.contain", "Take photo");
    cy.get(".registrations-section").should("not.exist");
  });
  it("Scan wrong code", () => {
    cy.loginAdmin(false);
    cy.visit("/scan-pass?code=XXXXXXXXXX");
    cy.contains("Invalid code");
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

      // Check taking a photo
      cy.get('img[alt="contact photo"]').should("not.exist");
      cy.contains("Take photo").click();
      cy.get("[role=dialog] video").should("be.visible");
      cy.get("[role=dialog] button").contains("Capture").click();
      cy.get('img[alt="contact photo"]').should("be.visible");

      // Check cropping the photo
      cy.contains("Crop photo").click();
      cy.get("[role=dialog] button").contains("Crop").click();
      cy.get('img[alt="contact photo"]').should("be.visible");

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
