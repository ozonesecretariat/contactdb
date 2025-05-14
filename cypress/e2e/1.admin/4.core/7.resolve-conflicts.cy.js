describe("Check resolve conflicts", () => {
  it("Check search conflicts", () => {
    cy.loginEdit();
    cy.checkSearch({
      expectedValue: "Mr. Aurora Astra (Exøplănetâry Çolönizàtion Áuțhôrîtÿ, Estonia)",
      modelName: "Resolve conflicts",
      searchValue: "ireland exoplanetary",
    });
  });
});
