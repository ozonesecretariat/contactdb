describe("Check", () => {
  it("Check search", () => {
    cy.loginAdmin();
    cy.checkSearch({
      modelName: "Send email tasks",
      searchValue: "placeholder atlas drake",
      expectedValue: "Test placeholder email",
    });

    cy.task("cleanDownloadsFolder");
    cy.get("a").contains("Download").click();
    cy.checkFile({
      filePattern: "75bf59cd-bede-4149-ba4b-7bd1a6f90312.eml",
      expected: [
        "Test placeholder email",
        "Dear Atlas Drake",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit",
        "Kind Regards",
      ],
    });
  });
  it("Check contact link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Send email tasks",
      searchValue: "placeholder atlas drake",
    });
    cy.get("a").contains("Atlas Drake (Deep Space Exploration Agency, Jamaica)").click();
    cy.contains("Change contact");
  });
});
