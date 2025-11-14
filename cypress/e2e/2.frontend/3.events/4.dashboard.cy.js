describe("Check dashboard page", () => {
  it("Check charts by status", () => {
    cy.loginAdmin(false);
    cy.checkNavActive("Dashboard");
    cy.checkChart("Total Participants", ["Nominated is 3", "Accredited is 7", "Registered is 10", "Revoked is 0"]);
    cy.checkChart("Participants by Organization Type", [
      "The 0 series is a Bar chart representing Nominated.",
      "The 1 series is a Bar chart representing Accredited.",
      "The 2 series is a Bar chart representing Registered.",
      "The 3 series is a Bar chart representing Revoked.",
    ]);
    cy.checkChart("Participants by Organization Type", [
      // type is value for series, index in series, total
      "Parties is 1, 0, 1",
      "Parties is 1, 0, 2",
      "Parties is 4, 0, 6",
      "Parties is 0, 0, 6",
    ]);
    cy.checkChart("Participants by Region", [
      // type is index, value for series
      "A5 is 1, 3",
      "A5 is 1, 6",
      "A5 is 1, 9",
      "A5 is 1, 0",
    ]);
    cy.checkChart("A5 Participants", [
      // type is value for series, index in series, total
      "Central America is 1, 2, 1",
      "Central America is 1, 2, 2",
      "Central America is 4, 2, 6",
      "Central America is 0, 2, 6",
    ]);
  });
  it("Check charts by role", () => {
    cy.loginAdmin(false);
    cy.checkNavActive("Dashboard");
    cy.chooseQSelect("Group by", "Role");
    cy.checkChart("Total Participants", [
      "Head is 6",
      "Alternate Head is 6",
      "Delegate is 3",
      "Unofficial Delegate is 5",
    ]);
    cy.checkChart("Participants by Organization Type", [
      "The 0 series is a Bar chart representing Head.",
      "The 1 series is a Bar chart representing Alternate Head.",
      "The 2 series is a Bar chart representing Delegate.",
      "The 3 series is a Bar chart representing Unofficial Delegate.",
    ]);
    cy.checkChart("Participants by Organization Type", [
      // type is value for series, index in series, total
      "Parties is 3, 0, 3",
      "Parties is 2, 0, 5",
      "Parties is 0, 0, 5",
      "Parties is 1, 0, 6",
    ]);
    cy.checkChart("Participants by Region", [
      // type is index, value for series
      "A5 is 1, 6",
      "A5 is 1, 5",
      "A5 is 1, 3",
      "A5 is 1, 4",
    ]);
    cy.checkChart("A5 Participants", [
      // type is value for series, index in series, total
      "Central America is 3, 2, 3",
      "Central America is 2, 2, 5",
      "Central America is 1, 2, 6",
      "Central America is 0, 2, 6",
    ]);
  });
  it("Go to Dashboard via url", () => {
    cy.loginAdmin(false);
    cy.visit("/dashboard?eventCode=SSMF&group=role&status=Nominated");
    cy.checkNavActive("Dashboard");
    cy.checkChart("Total Participants", [
      "Head is 3",
      "Alternate Head is 2",
      "Delegate is 1",
      "Unofficial Delegate is 5",
    ]);
    // Check Tooltip
    cy.get('[aria-label="Total Participants"] text').contains("Head").click();
    cy.get('[aria-label="Total Participants"] div').contains("3");
  });
});
