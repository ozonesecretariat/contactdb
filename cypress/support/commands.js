import path from "path";

import { randomStr } from "./utils";

function exists(val) {
  if (val) {
    return "exist";
  }
  return "not.exist";
}

function forceArray(val) {
  if (Array.isArray(val)) {
    return val;
  }
  return [val];
}

Cypress.Commands.addAll({
  addModel(modelName, fields) {
    cy.goToModelAdd(modelName);
    cy.fillInputs(fields);
    cy.get("input[value=Save]").click();
    cy.contains("was added successfully");
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
  checkExport({ expected = [], filePattern, filters = {}, modelName, searchValue = "" }) {
    cy.task("cleanDownloadsFolder");
    cy.performSearch({ filters, modelName, searchValue });
    cy.get("a").contains("Export").click();
    cy.fillInput("format", "csv");
    cy.get("[type=submit]").contains("Submit").click();
    cy.checkFile({ expected, filePattern, lineLength: expected.length + 1 });
  },
  checkFile({ expected, filePattern, lineLength = null }) {
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
  checkModelAdmin({
    checkDelete = true,
    extraFields = {},
    filters = {},
    modelName,
    nameField = "name",
    searchValue = null,
    suffix = "",
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
      cy.checkNotFound({ filters, modelName, searchValue: identifier });
    }
    return cy.wrap(fields);
  },
  checkNav(label) {
    return cy.get(".q-drawer [role=listitem]").contains(label);
  },
  checkNavActive(label) {
    return cy.get(".q-router-link--exact-active").contains(label);
  },
  checkNotFound({ filters = {}, modelName, searchValue = "" }) {
    cy.performSearch({ filters, modelName, searchValue });
    cy.contains("0 results");
  },
  checkSearch({ expectedValue = null, filters = {}, modelName, searchValue = "" }) {
    const checkedValue = expectedValue ?? searchValue;

    cy.performSearch({ filters, modelName, searchValue });
    cy.contains("1 result");
    cy.get("#result_list a").contains(checkedValue).click();
    cy.contains(checkedValue);
  },
  chooseSelect2(name, values) {
    cy.get(`[name=${name}]`).then(($el) => {
      const elId = $el.attr("id");
      for (const val of forceArray(values)) {
        cy.get(`[name=${name}]`).parent().find(".select2").click();
        cy.get(`[type=search][aria-controls="select2-${elId}-results"]`).type(val);
        cy.get(`#select2-${elId}-results [role=option]`).contains(val).click();
      }
    });
  },
  createContactGroup(numberOfContacts = 1, extraFields = {}) {
    const groupName = randomStr("test-group-");
    cy.addModel("Contact groups", { name: groupName });

    const contacts = [];
    for (let i = 0; i < numberOfContacts; i += 1) {
      const contact = {
        Contact_groups: [{ contactgroup: groupName }],
        emails: randomStr("test-email-", 10, "@example.org"),
        first_name: randomStr(`${i}-first-name-`),
        last_name: randomStr(`${i}-last-name-`),
        ...extraFields,
      };
      contacts.push(contact);

      cy.addModel("Contacts", contact);
    }

    return cy.wrap({ contacts, name: groupName });
  },
  createOrganizationType(numberOfOrganizations = 1, extraFields = {}) {
    const orgType = randomStr("test-type-");
    cy.addModel("Organization types", { acronym: orgType, title: orgType });

    const organizations = [];
    for (let i = 0; i < numberOfOrganizations; i += 1) {
      const org = {
        name: randomStr("test-org-", 10),
        organization_type: orgType,
        ...extraFields,
      };
      organizations.push(org);

      cy.addModel("Organizations", org);
    }

    return cy.wrap({ organizations, title: orgType });
  },
  deleteContactGroup(group) {
    cy.triggerAction({
      action: "Delete selected contacts",
      filters: { groups__in: group.name },
      modelName: "Contacts",
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
    cy.contains("Successfully deleted");

    cy.deleteModel("Contact groups", group.name);
  },
  deleteModel(modelName, searchValue, filters = {}) {
    cy.checkSearch({ filters, modelName, searchValue });
    cy.get("a").contains("Delete").click();
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
    cy.contains("deleted successfully");
  },
  deleteOrganizationType(orgType) {
    cy.triggerAction({
      action: "Delete selected organizations",
      filters: { organization_type__in: [orgType.title] },
      modelName: "Organizations",
    });
    cy.get("[type=submit]").contains("Yes, I’m sure").click();
    cy.contains("Successfully deleted");

    cy.deleteModel("Organization types", orgType.title);
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
        if (el.querySelector("fieldset.collapse details:not([open])")) {
          // If this inline is collapsible and not opened yet, click it first to open it.
          cy.wrap(el).click();
        }
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
  getIframeBody(selector) {
    return cy.get(selector).its("0.contentDocument.body").should("not.be.empty").then(cy.wrap);
  },
  goToModel(modelName) {
    cy.get("tbody a").contains(modelName).click();
  },
  goToModelAdd(modelName) {
    cy.goToModel(modelName);
    cy.get(".object-tools a.addlink").contains("Add").click();

    if (modelName === "Emails" || modelName === "Email templates") {
      cy.waitForCKEditor();
    }
  },
  login(user, password, checkSuccess = true, goToAdmin = true) {
    cy.visit("/");
    cy.get("input[autocomplete=email]").type(user);
    cy.get("input[autocomplete=current-password]").type(password);
    cy.get("[type=submit]:not([hidden])").click();
    if (checkSuccess) {
      cy.get(`[data-user-email="${user}"]`);
    }
    if (checkSuccess && goToAdmin) {
      cy.get("a").contains("Admin").click();
    }
  },
  loginAdmin(goToAdmin = true) {
    cy.login("admin@example.com", "admin", true, goToAdmin);
  },
  loginEdit(goToAdmin = true) {
    cy.login("test-edit@example.com", "test", true, goToAdmin);
  },
  loginEmails(goToAdmin = true) {
    cy.login("test-emails@example.com", "test", true, goToAdmin);
  },
  loginKronos(goToAdmin = true) {
    cy.login("test-kronos@example.com", "test", true, goToAdmin);
  },
  loginNoAccess(goToAdmin = true) {
    cy.login("test-no-access@example.com", "test", true, goToAdmin);
  },
  loginNonStaff(goToAdmin = true) {
    cy.login("test-non-staff@example.com", "test", true, goToAdmin);
  },
  loginNonStaffNoAccess(goToAdmin = true) {
    cy.login("test-non-staff-no-access@example.com", "test", true, goToAdmin);
  },
  loginNonStaffView(goToAdmin = true) {
    cy.login("test-non-staff-view@example.com", "test", true, goToAdmin);
  },
  loginView(goToAdmin = true) {
    cy.login("test-view@example.com", "test", true, goToAdmin);
  },
  performSearch({ filters = {}, modelName, searchValue = "" }) {
    cy.goToModel(modelName);
    cy.fillInputs(filters);
    if (searchValue) {
      cy.get("#searchbar").type(searchValue);
      cy.get("input[value=Search]").click();
    }
  },
  triggerAction({ action, filters = {}, modelName, searchValue = "" }) {
    cy.performSearch({ filters, modelName, searchValue });
    cy.fillInput("action", action);
    cy.get("#action-toggle").click();
    cy.get(".actions button").contains("Go").click();
  },
  waitForCKEditor() {
    // Tests can run faster than CKEditor can initialize. So wait for it to be done.
    cy.window().should((win) => {
      expect(win).to.have.property("CKEDITOR");
    });
  },
});

/**
 * Clicking on a link might open a new tab, for those cases use this command to keep the page
 * in the same tab. This is needed because cypress will ignore the newly open tab.
 */
Cypress.Commands.add("goToHref", { prevSubject: true }, (subject) =>
  cy
    .wrap(subject)
    .invoke("attr", "href")
    .then((href) => cy.visit(href)),
);
