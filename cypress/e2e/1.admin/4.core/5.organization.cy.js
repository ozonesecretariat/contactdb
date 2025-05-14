describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ extraFields: { organization_type: "OTHER" }, modelName: "Organizations" });
  });
  it("Check model search", () => {
    cy.loginView();
    cy.checkSearch({
      expectedValue: "Exøplănetâry Çolönizàtion Áuțhôrîtÿ",
      modelName: "Organizations",
      searchValue: "Exoplanetary Colonization Authority",
    });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      expected: ["Extraterrestrial Relations Bureau", "Intergalactic Defense Coalition"],
      filePattern: "Organization",
      filters: {
        country: "Uruguay",
      },
      modelName: "Organizations",
    });
  });
  it("Check contacts link", () => {
    cy.loginView();
    cy.performSearch({
      filters: {
        government: "Chile",
        organization_type: "Exhibitors",
      },
      modelName: "Organizations",
    });
    cy.contains("Quantum Entanglement Research Consortium");
    cy.get("a").contains("8 contacts").click();
    cy.contains("Select contact");
    cy.contains("8 results");
  });
});
