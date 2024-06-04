import { randomStr } from "./utils";
import path from "path";

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
  goToModel(modelName) {
    cy.get("tbody a").contains(modelName).click();
  },
  goToModelAdd(modelName) {
    cy.goToModel(modelName);
    cy.get(".object-tools a.addlink").contains("Add").click();
  },
  addModel(modelName, fields) {
    cy.goToModelAdd(modelName);
    cy.fillInputs(fields);
    cy.get("input[value=Save]").click();
    cy.contains("was added successfully");
  },
  deleteModel(modelName, searchValue, filters = {}) {
    cy.checkSearch({ modelName, searchValue, filters });
    cy.get("a").contains("Delete").click();
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
    cy.contains("deleted successfully");
  },
  chooseSelect2(name, value) {
    cy.get(`[name=${name}`).then(($el) => {
      const elId = $el.attr("id");
      cy.get(`[name=${name}]`).parent().find(".select2").click();
      cy.get(`[type=search][aria-controls="select2-${elId}-results"]`).type(value);
      cy.get(`#select2-${elId}-results [role=option]`).contains(value).click();
    });
  },
  getIframeBody(selector) {
    return cy.get(selector).its("0.contentDocument.body").should("not.be.empty").then(cy.wrap);
  },
  fillCKEditor(name, value) {
    cy.getIframeBody(`.field-${name} iframe`).type(value);
  },
  fillInline(name, values) {
    for (let i = 0; i < values.length; i += 1) {
      cy.get(`#${name}-group .add-row a`).click();

      for (const [key, value] of Object.entries(values[i])) {
        cy.fillInput([name, i, key].join("-"), value);
      }
    }
  },
  fillInput(name, value) {
    cy.get(`[name="${name}"], #${name}-group`).then(($el) => {
      const el = $el.get(0);

      if (el.tagName.toLowerCase() === "select") {
        if (el.classList.contains("admin-autocomplete")) {
          cy.chooseSelect2(name, value);
        } else {
          cy.get(`[name=${name}]`).select(value);
        }
      } else if (el.dataset.type === "ckeditortype") {
        cy.fillCKEditor(name, value);
      } else if (el.classList.contains("inline-group")) {
        cy.fillInline(name, value);
      } else if (el.type === "file") {
        cy.get(`[name="${name}"]`).first().selectFile(value);
      } else {
        cy.get(`[name="${name}"]`).first().type(value);
      }
    });
  },
  fillInputs(inputs) {
    for (const [key, value] of Object.entries(inputs)) {
      cy.fillInput(key, value);
    }
  },
  triggerAction({ modelName, action, searchValue = "", filters = {} }) {
    cy.performSearch({ modelName, searchValue, filters });
    cy.fillInput("action", action);
    cy.get("#action-toggle").click();
    cy.get(".actions button").contains("Go").click();
  },
  performSearch({ modelName, searchValue = "", filters = {} }) {
    cy.goToModel(modelName);
    cy.fillInputs(filters);
    if (searchValue) {
      cy.get("#searchbar").type(searchValue);
      cy.get("input[value=Search]").click();
    }
  },
  checkNotFound({ modelName, searchValue = "", filters = {} }) {
    cy.performSearch({ modelName, searchValue, filters });
    cy.contains("0 results");
  },
  checkSearch({ modelName, searchValue = "", expectedValue = null, filters = {} }) {
    const checkedValue = expectedValue ?? searchValue;

    cy.performSearch({ modelName, searchValue, filters });
    cy.contains("1 result");
    cy.get("#result_list a").contains(checkedValue).click();
    cy.contains(checkedValue);
  },
  checkModelAdmin({
    modelName,
    nameField = "name",
    extraFields = {},
    suffix = "",
    checkDelete = true,
    filters = {},
    searchValue = null,
  }) {
    let identifier = searchValue;
    const fields = { ...extraFields };

    if (nameField) {
      fields[nameField] = randomStr(`test-${modelName}-`, 10, suffix);
      identifier ??= fields[nameField];
    }
    cy.addModel(modelName, fields);
    if (checkDelete) {
      cy.deleteModel(modelName, identifier, filters);
      cy.checkNotFound({ modelName, searchValue: identifier, filters });
    }
    return cy.wrap(fields);
  },
  createContactGroup(numberOfContacts = 1, extraFields = {}) {
    const groupName = randomStr("test-group-");
    cy.addModel("Contact groups", { name: groupName });

    const contacts = [];
    for (let i = 0; i < numberOfContacts; i += 1) {
      const contact = {
        first_name: randomStr("first-name-"),
        last_name: randomStr("last-name-"),
        emails: randomStr("test-email-", 10, "@example.org"),
        Contact_groups: [{ contactgroup: groupName }],
        ...extraFields,
      };
      contacts.push(contact);

      cy.addModel("Contacts", contact);
    }

    return cy.wrap({ name: groupName, contacts });
  },
  deleteContactGroup(group) {
    cy.triggerAction({
      modelName: "Contacts",
      action: "Delete selected contacts",
      filters: { groups__in: group.name },
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
    cy.contains("Successfully deleted");

    cy.deleteModel("Contact groups", group.name);
  },
  checkFile({ filePattern, expected, lineLength = null }) {
    cy.verifyDownload(filePattern, { contains: true });
    cy.task("downloads").then((files) => {
      const downloadsFolder = Cypress.config("downloadsFolder");
      const fullPath = path.join(
        downloadsFolder,
        files.find((fn) => fn.includes(filePattern)),
      );

      cy.readFile(fullPath, "utf-8").then((content) => {
        if (lineLength) {
          expect(content.trim().split("\n")).to.have.length(lineLength);
        }
        for (const value of expected) {
          expect(content).to.contain(value);
        }
      });
    });
  },
  checkExport({ modelName, searchValue = "", filters = {}, filePattern, expected = [] }) {
    cy.task("cleanDownloadsFolder");
    cy.performSearch({ modelName, searchValue, filters });
    cy.get("a").contains("Export").click();
    cy.fillInput("file_format", "csv");
    cy.get("[type=submit]").contains("Submit").click();
    cy.checkFile({ filePattern, expected, lineLength: expected.length + 1 });
  },
});
