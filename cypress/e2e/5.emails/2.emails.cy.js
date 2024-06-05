import { randomStr } from "../../support/utils";

describe("Check", () => {
  it("Check send", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "Élàra Vãngüard",
        groups: "Literary Legends League",
        events: "Stéllâr Sérènade Müsïc Fêstivàl",
        content: "Test sending email",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });
  });
  it.only("Check send no CC address", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "John No CC email",
        content: "Test sending email with no CC",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });

    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
  });
  it("Check use template placeholder", () => {
    const subject = randomStr(`email-subject-`);
    cy.loginEmails();
    cy.goToModelAdd("Emails");
    cy.fillInputs({ recipients: "Aria-Eclipse Titan", subject });
    // Chose a template to fill the body
    cy.get("a.cke_button__templates").click();
    cy.get("a").contains("Test placeholders").click();
    cy.getIframeBody(".field-content iframe").contains("Dear [[full_name]");
    cy.get("input[value=Save]").click();

    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get("a").contains(subject).click();

    // Check placeholder interpolation in preview
    cy.get("#fieldsetcollapser0").click();
    cy.getIframeBody(".field-email_preview iframe").contains("Dear Mrs. Aria-Eclipse Titan");
    cy.get(".field-email_plaintext").contains("Dear Mrs. Aria-Eclipse Titan");
    // Check placeholder interpolation in the raw email
    cy.get("#fieldsetcollapser1").click();
    cy.get(".field-email_source").contains("Dear Mrs. Aria-Eclipse Titan");
  });
  it("Check inline image", () => {
    const subject = randomStr(`email-subject-`);
    cy.loginEmails();
    cy.goToModelAdd("Emails");
    cy.fillInputs({ recipients: "Aria-Eclipse Titan", subject });
    // Chose an image and upload it
    cy.get("a.cke_button__image").click();
    cy.get("a").contains("Upload").click();
    cy.getIframeBody(".cke_dialog_ui_input_file iframe")
      .find("input[name=upload]")
      .selectFile("fixtures/test/files/test-logo.png");
    cy.get("a").contains("Send it to the Server").click();
    cy.get("a").contains("OK").click();
    cy.getIframeBody(".field-content iframe").find("img").should("be.visible");
    cy.get("input[value=Save]").click();

    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get("a").contains(subject).click();
    //
    // Check image is shown in preview
    cy.get("#fieldsetcollapser0").click();
    cy.getIframeBody(".field-email_preview iframe").find("img").should("be.visible");

    // Check image is included in the raw HTML body of the email
    cy.get("#fieldsetcollapser1").click();
    cy.get(".field-email_source").contains('src="http://');
    cy.get(".field-email_source").contains("media/uploads");
    cy.get(".field-email_source").contains("test-logo");
  });
  it("Check use attachments", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "Aria-Eclipse Titan",
        content: "Test sending email with attachments",
        attachments: [{ file: "fixtures/test/files/lorem-ipsum.txt" }],
      },
      suffix: "-email-subject",
      checkDelete: false,
    });
    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get("#result_list tbody th a").click();

    // Check download attachment
    cy.task("cleanDownloadsFolder");
    cy.get("#fieldsetcollapser0").click();
    cy.get("a").contains("lorem-ipsum.txt").click();
    cy.checkFile({
      filePattern: "lorem-ipsum",
      expected: ["Lorem ipsum dolor sit amet, consectetur adipiscing elit"],
    });

    // Check attachment in the raw email
    cy.get("#fieldsetcollapser1").click();
    cy.get(".field-email_source").contains("lorem-ipsum.txt");
    cy.get(".field-email_source").contains("Lorem ipsum dolor sit amet, consectetur adipiscing elit");
  });
  it("Check success link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("19 emails").click();
    cy.contains("Select send email task");
    cy.contains("MP Nyx Spectrum");
    cy.contains("19 results");
  });
  it("Check failure link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("5 emails").click();
    cy.contains("Select send email task");
    cy.contains("Ms. Astrid-Cassius Galactic");
    cy.contains("5 results");
  });
  it("Check pending link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("6 emails").click();
    cy.contains("Select send email task");
    cy.contains("Mr. Rigel Zephyr");
    cy.contains("6 results");
  });
});
