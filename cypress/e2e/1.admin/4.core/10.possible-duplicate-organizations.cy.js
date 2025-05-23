import { randomStr } from "../../../support/utils";

describe("Check possible duplicate organizations", () => {
  it("Check search", () => {
    cy.loginEdit();
    cy.checkSearch({
      expectedValue: "Name and government: advanced quantum computing institute, chile",
      modelName: "Possible duplicate organizations",
      searchValue: "Institute Chile",
    });
    cy.contains("Advanced Quantum Computing Institute, Chile");
  });
  it("Check dismiss", () => {
    const orgName = randomStr("duplicate-check-org-");
    cy.loginEdit();
    cy.createOrganizationType(2, {
      government: "Spain",
      name: orgName,
    }).then((orgType) => {
      cy.checkSearch({
        expectedValue: `Name and government: ${orgName.toLowerCase()}, spain`,
        filters: { organizations__organization_type: orgType.title },
        modelName: "Possible duplicate organizations",
        searchValue: orgName,
      });
      cy.get("a").contains("Dismiss").click();
      cy.checkNotFound({
        filters: { organizations__organization_type: orgType.title },
        modelName: "Possible duplicate organizations",
      });
      cy.checkSearch({
        expectedValue: `Name and government: ${orgName.toLowerCase()}, spain`,
        filters: {
          is_dismissed: "Yes",
          organizations__organization_type: orgType.title,
        },
        modelName: "Possible duplicate organizations",
      });

      cy.deleteOrganizationType(orgType);
    });
  });
  it("Check dismiss bulk", () => {
    const orgName = randomStr("duplicate-check-org-bulk-");

    cy.loginEdit();
    cy.createOrganizationType(2, {
      government: "Spain",
      name: orgName,
    }).then((orgType) => {
      cy.triggerAction({
        action: "Dismiss selected duplicates",
        modelName: "Possible duplicate organizations",
        searchValue: orgName,
      });
      cy.checkNotFound({ modelName: "Possible duplicate organizations", searchValue: orgName });
      cy.checkSearch({
        expectedValue: `Name and government: ${orgName.toLowerCase()}, spain`,
        filters: {
          is_dismissed: "Yes",
          organizations__organization_type: orgType.title,
        },
        modelName: "Possible duplicate organizations",
      });
      cy.deleteOrganizationType(orgType);
    });
  });
});
