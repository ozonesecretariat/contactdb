describe("Check DSA", () => {
  it("Go to DSA via url", () => {
    cy.loginDSA(false);
    cy.visit("/delegates?eventCode=SS:CCC&paidDsa=false&tag=online&status=Nominated");
    cy.get("header").contains("Delegates");
    cy.contains("1-1 of 1");
    cy.contains("Orion-Spectrum");
    cy.contains("Nova");
    cy.contains("Belarus");
  });
  it("Check filtering records", () => {
    cy.loginDSA(false);
    cy.contains("Delegates").click();
    cy.get("header").contains("Delegates");
    cy.contains("Records per page");

    cy.chooseQSelect("Event", "Spectrum Symposium: Colorful Conference on Creativity");
    cy.chooseQSelect("Paid DSA", "No");
    cy.chooseQSelect("Status", "Nominated");
    cy.chooseQSelect("Tag", "online");
    cy.contains("1-1 of 1");
    cy.contains("Orion-Spectrum");
    cy.contains("Nova");
    cy.contains("Belarus");
  });
  it("Check filtering by code", () => {
    cy.loginDSA(false);
    cy.contains("Delegates").click();
    cy.get("header").contains("Delegates");
    cy.contains("Records per page");

    cy.chooseQSelect("Event", "Spectrum Symposium: Colorful Conference on Creativity");
    cy.get("input[name=priorityPassCode]").type("BZJC1ERFAX");
    cy.contains("1-1 of 1");
    cy.contains("Orion-Spectrum");
    cy.contains("Nova");
    cy.contains("Belarus");
  });
  it("Check create DSA", () => {
    cy.loginAdmin();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.addModel("Registrations", {
        contact: contact.last_name,
        event: "Yoga Experience",
        role: "Alternate Head",
        status: "Registered",
      });
      // Go to DSA page
      cy.contains("View site").click();
      cy.contains("Delegates").click();
      cy.get("header").contains("Delegates");
      cy.contains("Records per page");
      // Find our contact
      cy.chooseQSelect("Event", "Yoga Experience");
      cy.get("input[name=search]").type(contact.last_name);
      cy.contains("1-1 of 1");
      cy.contains(contact.first_name);
      // Open the edit modal
      cy.get("tbody tr").click();
      cy.get("input[name=umojaTravel]").type("12");
      cy.get("input[name=bp]").type("34");
      cy.get("input[name=arrivalDate]").type("2025-09-01");
      cy.get("input[name=departureDate]").type("2025-09-11");
      cy.get("input[name=cashCard]").type("56");
      cy.get('[role="checkbox"][aria-label="Paid DSA"]').click();
      cy.chooseQSelect("Tags", "Is funded");
      // Upload files
      cy.get("input[name=passport]").selectFile("fixtures/test/files/test-logo.png");
      cy.get("input[name=boardingPass]").selectFile("fixtures/test/files/test-logo.png");
      // Take photo
      cy.get('[name=signature] [aria-label="Take photo"]').click();
      cy.get("[role=dialog] video").should("be.visible");
      cy.get("[role=dialog] .q-inner-loading").should("not.exist");
      cy.get("[role=dialog] button").contains("Capture").click();

      // Save DSA and Registration
      cy.get("[type=submit]").click();
      cy.get("[role=dialog]").should("not.exist");

      // Go to Paid DSA page
      cy.checkNav("Paid DSA").click();
      cy.checkNavActive("Paid DSA");
      cy.chooseQSelect("Event", "Yoga Experience");
      cy.get("input[name=search]").type(contact.last_name);
      cy.contains("1-1 of 1");

      // Validated details
      cy.contains("12");
      cy.contains("34");
      cy.contains("56");
      cy.contains("10"); // nr of days
      cy.contains("4840"); // dsa days * 484
      cy.contains("416"); // termExp
      cy.contains("5256"); // total
      cy.contains("Sep 1, 2025");
      cy.contains("Sep 11, 2025");
      cy.get("td a").contains("Passport").click();
      cy.checkFile({ filePattern: "test-logo.png" });
      cy.get("td a").contains("Signature").click();
      cy.checkFile({ filePattern: "capture-" });

      // Cleanup
      cy.get("a").contains("Admin").click();
      cy.deleteContactGroup(group);
    });
  });
  it("Check edit DSA", () => {
    cy.loginAdmin();
    cy.createContactGroup().then((group) => {
      const contact = group.contacts[0];
      cy.addModel("Registrations", {
        contact: contact.last_name,
        event: "Yoga Experience",
        role: "Alternate Head",
        status: "Registered",
      });
      // Go to DSA page
      cy.contains("View site").click();
      cy.contains("Delegates").click();
      cy.get("header").contains("Delegates");
      cy.contains("Records per page");
      // Find our contact
      cy.chooseQSelect("Event", "Yoga Experience");
      cy.get("input[name=search]").type(contact.last_name);
      cy.contains("1-1 of 1");
      cy.contains(contact.first_name);
      // Open the edit modal
      cy.get("tbody tr").click();
      cy.get('[role="checkbox"][aria-label="Paid DSA"]').click();
      cy.get("input[name=umojaTravel]").type("123456");
      cy.get("input[name=bp]").type("67589");
      cy.chooseQSelect("Tags", "Is funded");
      // Save and validate
      cy.get("[type=submit]").click();
      cy.get("[role=dialog]").should("not.exist");
      cy.contains("123456");
      // Open again to start editing
      cy.get("tbody tr").click();

      cy.get("input[name=departureDate]").type("2025-09-11");
      cy.get("[type=submit]").click();
      cy.checkQInputError("arrivalDate", "Cannot specify departure date without arrival date.");

      cy.get("input[name=arrivalDate]").type("2025-09-21");
      cy.get("[type=submit]").click();
      cy.checkQInputError("arrivalDate", "Departure date cannot be before arrival date.");

      cy.get("input[name=arrivalDate]").clear();
      cy.get("input[name=arrivalDate]").type("2025-09-01");
      cy.get("[type=submit]").click();

      cy.get("[role=dialog]").should("not.exist");

      // Go to Paid DSA page and validate
      cy.visit(`/paid?eventCode=ZZ:SYE&paidDsa=true&tag=Is+funded&status=Registered&search=${contact.last_name}`);
      cy.checkNavActive("Paid DSA");
      cy.contains("10"); // nr of days
      cy.contains("4840"); // dsa days * 484
      cy.contains("416"); // termExp
      cy.contains("5256"); // total

      // Cleanup
      cy.get("a").contains("Admin").click();
      cy.deleteContactGroup(group);
    });
  });
});
