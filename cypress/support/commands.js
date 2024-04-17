import { randomStr } from "./utils";

function exists(val) {
  if (val) {
    return "exist";
  }
  return "not.exist";
}

Cypress.Commands.addAll({
  login(user, password, checkSuccess = true) {
    cy.visit(`/account/login/`);
    cy.get("input[autocomplete=username]").type(user);
    cy.get("input[autocomplete=current-password]").type(password);
    cy.get("input[type=submit]:not([hidden])").click();
    if (checkSuccess) {
      cy.contains(`Welcome, ${user}`);
    }
  },
  loginAdmin() {
    cy.login("admin@example.com", "admin");
  },
  loginEdit() {
    cy.login("test-edit@example.com", "test");
  },
  loginEmails() {
    cy.login("test-emails@example.com", "test");
  },
  loginKronos() {
    cy.login("test-kronos@example.com", "test");
  },
  loginNoAccess() {
    cy.login("test-no-access@example.com", "test");
  },
  loginView() {
    cy.login("test-view@example.com", "test");
  },
  checkAccess(accessSpec) {
    cy.get("#content-main").then(($mainContent) => {
      const remainingApps = {};
      $mainContent.find(".module").each((i, appModule) => {
        const [, appName] = Array.from(appModule.classList)
          .find((className) => className.startsWith("app-"))
          .split("-");
        remainingApps[appName] = new Set();

        for (const modelRow of appModule.querySelectorAll("tbody tr")) {
          const [, modelName] = Array.from(modelRow.classList)
            .find((className) => className.startsWith("model-"))
            .split("-");

          remainingApps[appName].add(modelName);
        }
      });

      for (const [appName, models] of Object.entries(accessSpec)) {
        expect(remainingApps, `Expecting to find ${appName} in list of apps`).to.have.property(appName);
        const remainingModels = remainingApps[appName];
        delete remainingModels[appName];

        for (const [modelName, accessLevels] of Object.entries(models)) {
          remainingModels.delete(modelName);

          cy.get(`.app-${appName} .model-${modelName} th:first-of-type a`).should(
            exists(accessLevels === true || accessLevels.view),
          );
          cy.get(`.app-${appName} .model-${modelName} a.addlink`).should(
            exists(accessLevels === true || accessLevels.add),
          );
          cy.get(`.app-${appName} .model-${modelName} a.changelink`).should(
            exists(accessLevels === true || accessLevels.change),
          );
        }

        expect(Array.from(remainingModels), `Expecting all models to be checked for ${appName}`).to.be.empty;
      }

      expect(Array.from(remainingApps), "Expecting all apps to be checked").to.be.empty;
    });
  },
  chooseSelect(name, value) {
    cy.get(`.field-${name} .select2`).click();
    cy.get(`.select2-search  [type=search]`).type(value);
    cy.get(`.select2-results [role=option]`).contains(value).click();
  },
  getIframeBody(selector) {
    return cy.get(selector).its("0.contentDocument.body").should("not.be.empty").then(cy.wrap);
  },
  typeCKEditor(name, value) {
    cy.getIframeBody(`.field-${name} iframe`).type(value);
  },
  checkSearch(modelName, searchValue, expectedValue = null) {
    const checkedValue = expectedValue ?? searchValue;

    cy.get("a").contains(modelName).click();
    cy.get("#searchbar").type(searchValue);
    cy.get("input[value=Search]").click();
    cy.contains("1 result");
    cy.get("a").contains(checkedValue).click();
    cy.get("h2").contains(checkedValue);
  },
  checkAdd(modelName, nameField = "name", extraFields = {}, suffix = "") {
    const randomName = randomStr(`test-${modelName}-`, 64, suffix);

    cy.get("a").contains(modelName).click();
    cy.get(".object-tools a.addlink").contains("Add").click();
    cy.get(`[name="${nameField}"]`).type(randomName);

    for (const [name, value] of Object.entries(extraFields)) {
      cy.get(`[name="${name}"]`).then(($el) => {
        const el = $el.get(0);

        if (el.tagName.toLowerCase() === "select") {
          cy.chooseSelect(name, value);
        } else if (el.dataset.type === "ckeditortype") {
          cy.typeCKEditor(name, value);
        } else {
          cy.get(`[name="${name}"]`).type(value);
        }
      });
    }
    cy.get("input[value=Save]").click();
    cy.get("#searchbar").type(randomName);
    cy.get("input[value=Search]").click();
    cy.contains("1 result");

    cy.get("#result_list a").contains(randomName).click();
    cy.get("h2").contains(randomName);

    cy.get("a").contains("Delete").click();
    cy.get("[type=submit]").contains("Yes, I’m sure").click();

    cy.get("#searchbar").type(randomName);
    cy.get("input[value=Search]").click();
    cy.contains("0 results");
  },
});
