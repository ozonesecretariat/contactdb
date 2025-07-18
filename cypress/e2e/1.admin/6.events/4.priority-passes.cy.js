describe("Check", () => {
  it("Check model admin", () => {
    cy.loginView();
    cy.checkSearch({ modelName: "Priority passes", searchValue: "T6UQZRYW0S" });
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("QQ:ASAS Quantum Quest: A Science Adventure Symposium");
    cy.contains("PDAF Psychedelic Dreamscape Art Fair");
    cy.contains("SSMF Stéllâr Sérènade Müsïc Fêstivàl");
  });
  it("Check scan view", () => {
    cy.loginEdit();
    visitAdmin("/admin/events/prioritypass/pass-scan-view/?code=T6UQZRYW0S");
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("QQ:ASAS Quantum Quest: A Science Adventure Symposium");
    cy.contains("PDAF Psychedelic Dreamscape Art Fair");
    cy.contains("SSMF Stéllâr Sérènade Müsïc Fêstivàl");
  });
  it("Check scan view wrong code", () => {
    cy.loginEdit();
    visitAdmin("/admin/events/prioritypass/pass-scan-view/?code=XXXXXXXXXX");
    cy.contains("Priority pass does not exist");
  });
  it("Check scan view no code", () => {
    cy.loginEdit();
    visitAdmin("/admin/events/prioritypass/pass-scan-view/");
    cy.contains("No priority pass code provided");
  });
  it("Check save and send email with priority pass", () => {
    cy.loginAdmin();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.checkModelAdmin({
        checkDelete: false,
        extraFields: {
          contact: contact.last_name,
          event: "Psychedelic Dreamscape Art Fair",
          role: "Alternate Head",
          status: "Accredited",
        },
        filters: {
          event: "Psychedelic Dreamscape Art Fair",
        },
        modelName: "Registrations",
        nameField: null,
        searchValue: contact.last_name,
      });
      // Go to priority pass and send it
      cy.performSearch({ modelName: "Priority passes", searchValue: contact.last_name });
      cy.contains("1 priority pass");
      cy.get(".field-code a").click();
      cy.contains("PDAF Psychedelic Dreamscape Art Fair");
      cy.contains("Save and send").click();
      cy.contains("1 confirmation emails have been queued for sending");
      cy.performSearch({ modelName: "Send email tasks", searchValue: contact.last_name });
      // Wait for the task to finish
      cy.reloadUntilText(".paginator", "1 send email task");
      cy.get(".field-status_display").contains("SUCCESS");
      cy.get(".field-email a").click();
      // Check priority pass was attached
      cy.get(".field-email_attachments a[download]").contains(".pdf");
      cy.deleteContactGroup(group);
    });
  });
  it("Check save and send email without priority pass", () => {
    cy.loginAdmin();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.checkModelAdmin({
        checkDelete: false,
        extraFields: {
          contact: contact.last_name,
          event: "Enigma Expo: Unraveling Mysteries Convention",
          role: "Alternate Head",
          status: "Accredited",
        },
        filters: {
          event: "Enigma Expo: Unraveling Mysteries Convention",
        },
        modelName: "Registrations",
        nameField: null,
        searchValue: contact.last_name,
      });
      // Go to priority pass and send it
      cy.performSearch({ modelName: "Priority passes", searchValue: contact.last_name });
      cy.contains("1 priority pass");
      cy.get(".field-code a").click();
      cy.contains("EE:UMC Enigma Expo: Unraveling Mysteries Convention");
      cy.contains("Save and send").click();
      cy.contains("1 confirmation emails have been queued for sending");
      cy.performSearch({ modelName: "Send email tasks", searchValue: contact.last_name });
      // Wait for the task to finish
      cy.reloadUntilText(".paginator", "1 send email task");
      cy.get(".field-status_display").contains("SUCCESS");
      cy.get(".field-email a").click();
      // Check priority pass was not attached
      cy.get(".field-email_attachments a[download]").should("not.exist");
      cy.deleteContactGroup(group);
    });
  });
});

function visitAdmin(visitUrl) {
  cy.url().then((currentUrl) => {
    const url = new URL(currentUrl);
    cy.visit(`${url.protocol}//${url.host}${visitUrl}`);
  });
}
