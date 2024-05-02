describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({ modelName: "Organizations", extraFields: { organization_type: "OTHER" } });
  });
  it("Check export", () => {
    cy.loginView();
    cy.checkExport({
      modelName: "Organizations",
      filters: {
        country: "Uruguay",
      },
      filePattern: "Organization",
      expected: ["Extraterrestrial Relations Bureau", "Intergalactic Defense Coalition"],
    });
  });
  it("Check contacts link", () => {
    cy.loginView();
    cy.performSearch({
      modelName: "Organizations",
      filters: {
        organization_type: "Exhibitors",
        government: "Chile",
      },
    });
    cy.contains("Quantum Entanglement Research Consortium");
    cy.get("a").contains("8 contacts").click();
    cy.contains("Select contact");
    cy.contains("8 results");
  });
});
