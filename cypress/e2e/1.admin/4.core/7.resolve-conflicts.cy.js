describe("Check resolve conflicts", () => {
  it("Check search conflicts", () => {
    cy.loginEdit();
    cy.checkSearch({
      expectedValue: "Mr. Aurora Astra (Exøplănetâry Çolönizàtion Áuțhôrîtÿ, Guatemala)",
      modelName: "Resolve conflicts",
      searchValue: "ireland exoplanetary",
    });
  });
});
