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
});

function visitAdmin(visitUrl) {
  cy.url().then((currentUrl) => {
    const url = new URL(currentUrl);
    cy.visit(`${url.protocol}//${url.host}${visitUrl}`);
  });
}
