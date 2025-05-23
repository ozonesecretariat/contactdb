describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Contacts", nameField: "last_name" });
  });
  it("Check multiselect filter", () => {
    cy.loginView();
    cy.performSearch({
      filters: {
        country__in: ["Albania", "Chad"],
        groups__in: ["The Dream Team Connection", "Music Maniacs Association"],
        organization__in: ["Warp Dynamics Institute", "Galactic Research Institute for Advanced Technologies"],
        organization__organization_type__in: ["IGOs", "UN Agencies"],
      },
      modelName: "Contacts",
    });
    cy.contains("aria@example.com");
    cy.contains("axel-elio@example.com");
    cy.contains("2 results");
  });
  it("Check merge contacts", () => {
    cy.loginEdit();
    cy.createContactGroup(2).then((group) => {
      cy.triggerAction({
        action: "Merge selected contacts",
        filters: { groups__in: group.name },
        modelName: "Contacts",
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
        action: "Add selected contacts to group",
        filters: { groups__in: group.name },
        modelName: "Contacts",
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
      expected: ["astrid-cassius@example.com", "cassian-xenon@example.com"],
      filePattern: "Contact",
      filters: {
        country__in: "Liechtenstein",
      },
      modelName: "Contacts",
    });
  });
  it("Check import", () => {
    cy.loginEdit();
    cy.goToModel("Contacts");
    cy.get("a").contains("Import").click();
    cy.get("input[type=file][name=import_file]").selectFile("fixtures/test/files/test-contact-import.xlsx");
    cy.fillInput("format", "xlsx");
    cy.get("input[type=submit]").contains("Submit").click();
    cy.get("input[type=submit]").contains("Confirm import").click();
    cy.contains("Import finished: 2 new, 0 updated, 0 deleted and 0 skipped contacts.");

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
      action: "Delete selected contacts",
      filters: {
        country__in: "Nicaragua",
        groups__in: "Adventure Seekers Squad",
        organization__in: "Astral Technologies Syndicate",
      },
      modelName: "Contacts",
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
  });
  it("Check organization link", () => {
    cy.loginView();
    cy.performSearch({
      filters: {
        country__in: "Albania",
        organization__in: "Warp Dynamics Institute",
      },
      modelName: "Contacts",
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("Warp Dynamics Institute, Cuba").click();
    cy.contains("View organization");
    cy.contains("Warp Dynamics Institute, Cuba");
  });
  it("Check registrations link", () => {
    cy.loginView();
    cy.performSearch({
      filters: {
        country__in: "Albania",
        organization__in: "Warp Dynamics Institute",
      },
      modelName: "Contacts",
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("9 events").click();
    cy.contains("Select registration");
    cy.contains("Ms. Aria Quantum (Warp Dynamics Institute, Cuba)");
    cy.contains("9 results");
  });
  it("Check email log link", () => {
    cy.loginAdmin();
    cy.performSearch({
      filters: {
        country__in: "Albania",
        registrations__event: "Mythos Masquerade Ball",
      },
      modelName: "Contacts",
    });
    cy.contains("1 result");
    cy.contains("Aria");
    cy.contains("Quantum");
    cy.get("a").contains("Email Logs").click();
    cy.contains("Select send email task");
    cy.contains("Ms. Aria Quantum (Warp Dynamics Institute, Cuba)");
    cy.contains("2 results");
  });
  it("Check send email to contacts", () => {
    cy.loginAdmin();
    cy.triggerAction({
      action: "Send email to selected contacts",
      filters: {
        organization__in: "Quantum Engineering Consortium",
      },
      modelName: "Contacts",
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("Axel Nyx");
    cy.get(".select2-selection__choice").contains("Ms. Kai Spectrum");
  });
});
