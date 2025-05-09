describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Contacts", nameField: "last_name" });
  });
  it("Check multiselect filter", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Contacts",
      filters: {
        country__in: ["Albania", "Chad"],
        organization__in: ["Warp Dynamics Institute", "Galactic Research Institute for Advanced Technologies"],
        groups__in: ["The Dream Team Connection", "Music Maniacs Association"],
      },
    });
    cy.contains("aria@example.com");
    cy.contains("axel-elio@example.com");
    cy.contains("2 results");
  });
  it("Check merge contacts", () => {
    cy.loginEdit();
    cy.createContactGroup(2).then((group) => {
      cy.triggerAction({
        modelName: "Contacts",
        action: "Merge selected contacts",
        filters: { groups__in: group.name },
      });
      cy.checkSearch({ modelName: "Resolve conflicts", searchValue: group.contacts[0].last_name });
      cy.get("input[value=Save]").click();
      cy.contains("changed successfully");
      cy.checkNotFound({ modelName: "Resolve conflicts", searchValue: group.contacts[0].last_name });
      cy.deleteContactGroup(group);
    });
  });
  it("Check add contacts to group", () => {
    cy.loginEdit();
    cy.createContactGroup(2).then((group) => {
      cy.triggerAction({
        modelName: "Contacts",
        action: "Add selected contacts to group",
        filters: { groups__in: group.name },
      });
      cy.fillInput("group", "Focal point");
      cy.get("[type=submit]").contains("Add to group").click();
      cy.checkSearch({ modelName: "Contacts", searchValue: group.contacts[0].last_name });
      cy.contains(group.name);
      cy.checkSearch({ modelName: "Contacts", searchValue: group.contacts[1].last_name });
      cy.contains(group.name);
      cy.deleteContactGroup(group);
    });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Contacts",
      filters: {
        country__in: "Liechtenstein",
      },
      filePattern: "Contact",
      expected: ["astrid-cassius@example.com", "cassian-xenon@example.com"],
    });
  });
  it("Check import", () => {
    cy.loginEdit();
    cy.goToModel("Contacts");
    cy.get("a").contains("Import").click();
    cy.get("input[type=file][name=import_file]").selectFile("fixtures/test/files/test-contact-import.xlsx");
    cy.get("input[type=submit]").contains("Submit").click();
    cy.get("input[type=submit]").contains("Confirm import").click();
    cy.contains("Import finished: 2 new, 0 updated, 0 deleted and 1 skipped contacts.");

    // Check values got imported correctly
    cy.performSearch({
      modelName: "Contacts",
      searchValue: "tiny.knight@example.org",
    });
    cy.get("#result_list tbody tr:first-of-type th a").click();
    cy.contains("Astral Technologies Syndicate");
    cy.contains("Adventure Seekers Squad");
    cy.contains("Dr. Tiny Knight");
    cy.get('[name=emails][value="tiny.knight@example.org"]');
    cy.get('[name=emails][value="tiny.knight@example.net"]');

    // Remove the imported data
    cy.triggerAction({
      modelName: "Contacts",
      action: "Delete selected contacts",
      filters: {
        organization__in: "Astral Technologies Syndicate",
        groups__in: "Adventure Seekers Squad",
        country__in: "Poland",
      },
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
  });
  it("Check organization link", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Contacts",
      filters: {
        organization__in: "Warp Dynamics Institute",
        country__in: "Albania",
      },
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("Warp Dynamics Institute, Guatemala").click();
    cy.contains("View organization");
    cy.contains("Warp Dynamics Institute, Guatemala");
  });
  it("Check registrations link", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Contacts",
      filters: {
        organization__in: "Warp Dynamics Institute",
        country__in: "Albania",
      },
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("9 events").click();
    cy.contains("Select registration");
    cy.contains("Ms. Aria Quantum (Warp Dynamics Institute, Guatemala)");
    cy.contains("9 results");
  });
  it("Check email log link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Contacts",
      filters: {
        registrations__event: "Mythos Masquerade Ball",
        country__in: "Albania",
      },
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("Email Logs").click();
    cy.contains("Select send email task");
    cy.contains("Ms. Aria Quantum (Warp Dynamics Institute, Guatemala)");
    cy.contains("2 results");
  });
  it("Check send email to contacts", () => {
    cy.loginAdmin();
    cy.triggerAction({
      modelName: "Contacts",
      action: "Send email to selected contacts",
      filters: {
        organization__in: "Quantum Engineering Consortium",
      },
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("Axel Nyx");
    cy.get(".select2-selection__choice").contains("Ms. Kai Spectrum");
  });
});
