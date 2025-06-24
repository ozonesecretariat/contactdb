import { randomStr } from "../../../support/utils";

describe("Check nominations page", () => {
  it("Check nominations page group and gov invitation token", () => {
    cy.loginAdmin(false);
    cy.visit("/token/0a8a390b-c5a5-4ba0-a06e-a78097382bb4/nominations");
    cy.contains("1-7 of 7");
    cy.get("[role=search]").type("authority");
    cy.contains("1-3 of 3");
  });
  it("Check nominations no auth", () => {
    cy.visit("/token/0a8a390b-c5a5-4ba0-a06e-a78097382bb4/nominations");
    cy.contains("1-7 of 7");
    cy.get("[role=search]").type("authority");
    cy.contains("1-3 of 3");
  });
  it("Check nominations no token", () => {
    cy.visit("/token/xxx-xxx-xxx-xxx-xxxx/nominations");
    cy.contains("No data available");
  });
  it("Find existing contact", () => {
    cy.visit("/token/123e4567-e89b-12d3-a456-426614174000/nominations");
    cy.contains("Add Nomination").click();
    cy.get("[role=dialog] [role=search]").type("elio");
    cy.contains("1-1 of 1");
    cy.contains("Ms. Axel-Elio Neutron");
  });
  it("Check create contact and nominate", () => {
    const email = randomStr("new-contact-", 10, "@example.com");
    const lastName = randomStr();
    cy.visit("/token/123e4567-e89b-12d3-a456-426614174000/nominations");
    cy.contains("Add Nomination").click();
    // Create a new participant
    cy.contains("Create new").click();
    cy.get("input[name=emails]").type(email);
    cy.get("input[name=firstName]").type("John");
    cy.get("input[name=lastName]").type(lastName);
    cy.get("[aria-label=Organization]").click();
    cy.get("[role=option]").contains("Galactic Research Institute for Advanced Technologies").click();
    // Add passport info
    cy.get("[role=checkbox]:has([name=needsVisaLetter])").click();
    cy.get("[name=nationality]").type("klingon");
    cy.get("[name=passportNumber]").type("123456789");
    cy.get("[name=passportDateOfIssue]").type("2022-01-01");
    cy.get("[name=passportDateOfExpiry]").type("2025-01-01");
    cy.get("[name=passport]").selectFile("fixtures/test/files/test-logo.png");
    // Add the photo
    cy.get("[name=photo]").selectFile("fixtures/test/files/test-logo.png");
    cy.contains("Save").click();
    cy.contains("Nominate participant");
    // Add a nomination for the participant
    cy.get('[aria-label="Role of the participant"]').click();
    cy.get("[role=option]").contains("Delegate").click();
    cy.contains("Confirm nomination").click();
    cy.contains("Close").click();
    // Check that the new nomination was added and the store was reloaded
    cy.get("[role=search]").type(email);
    cy.contains("1-1 of 1");
    cy.get("[aria-label=Edit]").click();
    cy.contains(email);
    // Remove the nomination we just added
    cy.get("[role=switch][aria-checked=true]").click();
    cy.contains("Confirm nomination").click();
    cy.contains("Close").click();
    // Check it was removed
    cy.get("[role=search]").type(email);
    cy.contains("No data available");
  });
});
