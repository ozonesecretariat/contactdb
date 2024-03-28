Cypress.Commands.add("login", (user = "admin@example.com", password = "admin") => {
  cy.visit(`/account/login/`);
  cy.get("input[autocomplete=username]").type(user);
  cy.get("input[autocomplete=current-password]").type(password);
  return cy.get("input[type=submit]:not([hidden])").click();
});
