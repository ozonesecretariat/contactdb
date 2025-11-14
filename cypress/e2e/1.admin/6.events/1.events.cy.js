describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      extraFields: {
        dates: "18-20 April 2024",
        end_date_0: "2024-04-20",
        end_date_1: "00:00:00",
        start_date_0: "2024-04-18",
        start_date_1: "00:00:00",
        title: "test event",
        venue_city: "online",
        venue_country: "Romania",
      },
      modelName: "Events",
      nameField: "code",
    });
  });
  it("Check model search", () => {
    cy.loginView();
    cy.checkSearch({
      expectedValue: "Stéllâr Sérènade Müsïc Fêstivàl",
      modelName: "Events",
      searchValue: "stellar serenade music festival",
    });
  });
  it("Check export", () => {
    cy.loginAdmin();
    cy.checkExport({
      expected: [
        "Quantum Quest: A Science Adventure Symposium",
        "Spectrum Symposium: Colorful Conference on Creativity",
      ],
      filePattern: "Event",
      filters: {
        venue_country: "Afghanistan",
      },
      modelName: "Events",
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
      action: "Send email to participants of selected events",
      modelName: "Events",
      searchValue: "techno",
    });
    cy.contains("Add email");
    cy.get(".select2-selection__choice").contains("TT:VRAQ");
    cy.get(".select2-selection__choice").contains("TTTE");
  });
  it("Check download pre-statistics", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Events",
      searchValue: "NN:FDP",
    });
    cy.contains("1 result");
    cy.task("cleanDownloadsFolder");
    cy.get("a").contains("Pre Statistics").click();
    cy.checkFile({
      filePattern: "NN_FDP-pre-meeting-statistics.docx",
    });
  });
  it("Check download post-statistics", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Events",
      searchValue: "NN:FDP",
    });
    cy.contains("1 result");
    cy.task("cleanDownloadsFolder");
    cy.get("a").contains("Post Statistics").click();
    cy.checkFile({
      filePattern: "NN_FDP-post-meeting-statistics.docx",
    });
  });
  it("Check download list of participants", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Events",
      searchValue: "NN:FDP",
    });
    cy.contains("1 result");
    cy.task("cleanDownloadsFolder");
    cy.get("a").contains("LoP").click();
    cy.checkFile({
      filePattern: "NN_FDP-LoP.docx",
    });
  });
  it("Check download DSA", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Events",
      searchValue: "NN:FDP",
    });
    cy.contains("1 result");
    cy.task("cleanDownloadsFolder");
    cy.get("main a").contains("DSA Report").click();
    cy.checkFile({
      filePattern: "NN_FDP-DSA.xlsx",
    });
    cy.get("main a").contains("DSA Files").click();
    cy.checkFile({
      filePattern: "NN_FDP-DSA-files.zip",
    });
  });
});
