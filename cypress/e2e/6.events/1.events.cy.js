describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      modelName: "Events",
      nameField: "code",
      extraFields: {
        title: "test event",
        start_date_0: "2024-04-18",
        start_date_1: "00:00:00",
        end_date_0: "2024-04-20",
        end_date_1: "00:00:00",
        venue_country: "Romania",
        venue_city: "online",
        dates: "18-20 April 2024",
      },
    });
  });
  it("Check model search", () => {
    cy.loginView();
    cy.checkSearch({
      modelName: "Events",
      searchValue: "stellar serenade music festival",
      expectedValue: "Stéllâr Sérènade Müsïc Fêstivàl",
    });
  });
  it("Check export", () => {
    cy.loginAdmin();
    cy.checkExport({
      modelName: "Events",
      filters: {
        venue_country: "Afghanistan",
      },
      filePattern: "Event",
      expected: [
        "Quantum Quest: A Science Adventure Symposium",
        "Spectrum Symposium: Colorful Conference on Creativity",
      ],
    });
  });
  it("Check participants link", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Events",
      searchValue: "SS:CCC",
    });
    cy.contains("1 result");
    cy.get("a").contains("20 participants").click();
    cy.contains("Select registration");
    cy.contains("20 results");
  });
  it("Check send email", () => {
    cy.loginEmails();
    cy.triggerAction({
      modelName: "Events",
      action: "Send email to participants of selected events",
      searchValue: "techno",
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("TT:VRAQ");
    cy.get(".select2-selection__choice").contains("TTTE");
  });
});
