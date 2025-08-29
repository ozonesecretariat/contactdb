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
    cy.checkSearch({ modelName: "Priority passes", searchValue: "T6UQZRYW0S" });
    cy.get(".field-pass_download_link a").contains("Scan").goToHref();
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("Quantum Quest: A Science Adventure Symposium");
    cy.contains("Psychedelic Dreamscape Art Fair");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
  });
  it("Check view pass as html", () => {
    cy.loginEdit();
    visitAdmin("/admin/events/prioritypass/372/pass/");
    cy.contains("T6UQZRYW0S");
    cy.contains("Guatemala");
    cy.contains("Mr. Lyra-Pulse Solstice");
    cy.contains("Quantum Quest: A Science Adventure Symposium");
    cy.contains("Psychedelic Dreamscape Art Fair");
    cy.contains("Stéllâr Sérènade Müsïc Fêstivàl");
    cy.contains("Tashkent, Myanmar");
    cy.contains("THIS PASS DOES NOT GRANT ACCESS TO THE VENUE.");
  });
  it("Check view badge as html", () => {
    cy.loginEdit();
    visitAdmin("/admin/events/prioritypass/372/badge/");
    cy.contains("T6UQZRYW0S");
    cy.contains("Lyra-Pulse");
    cy.contains("Solstice");
    cy.contains("Guatemala");
    cy.contains("Parties");
    cy.contains("PDAF@2025");
    cy.get('img[alt="https://example.com?appstore"]');
    cy.get('img[alt="https://example.com?playstore"]');
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
