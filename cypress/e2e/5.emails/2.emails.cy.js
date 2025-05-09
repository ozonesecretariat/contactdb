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
  it("Check send Cc fields", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "Thane Seren",
        cc_recipients: "Xenon Zephyr",
        cc_groups: "Literary Legends League",
        content: "Testing sending email with Cc fields",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });
    // Check that only 1 email has been sent.
    cy.contains("1 send email task");
    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get(".field-email a").click();
    // Check the contacts
    cy.get(".field-contact").contains("Thane Seren");
    cy.get(".field-cc_contacts_links").contains("Mr. John No CC email");
    cy.get(".field-cc_contacts_links").contains("Mr. 𝓙𝓸𝓱𝓷 🂡⚛︎ ᴛʜᴇ Łøᶑϻïŉ Ğàẕⱷņτ🎵 Ɗřăçóŋ <🐉> ");
    // Check the email addresses
    cy.get(".field-email_to").contains("thane@example.com");
    cy.get(".field-email_to").contains("thane.seren@example.org");
    cy.get(".field-email_cc").contains("john.no-cc@example.com");
    cy.get(".field-email_cc").contains("ţēśţ.παράδειγμα+ó@उदाहरण例子παράδειγμαпример例.test");
  });
  it("Check send Bcc fields", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "Thane Seren",
        bcc_recipients: "Xenon Zephyr",
        bcc_groups: "Literary Legends League",
        content: "Testing sending email with Bcc fields",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });
    // Check that only 1 email has been sent.
    cy.contains("1 send email task");
    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get(".field-email a").click();
    // Check the contacts
    cy.get(".field-contact").contains("Thane Seren");
    cy.get(".field-bcc_contacts_links").contains("Mr. John No CC email");
    cy.get(".field-bcc_contacts_links").contains("Mr. 𝓙𝓸𝓱𝓷 🂡⚛︎ ᴛʜᴇ Łøᶑϻïŉ Ğàẕⱷņτ🎵 Ɗřăçóŋ <🐉> ");
    // Check the email addresses
    cy.get(".field-email_to").contains("thane@example.com");
    cy.get(".field-email_to").contains("thane.seren@example.org");
    cy.get(".field-email_bcc").contains("john.no-cc@example.com");
    cy.get(".field-email_bcc").contains("ţēśţ.παράδειγμα+ó@उदाहरण例子παράδειγμαпример例.test");
  });
  it("Check send no CC address", () => {
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
  it("Checking sending to contact with no name", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "no-name.jane",
        content: "Dear [[full_name]],\nYou don't actually have a name!?!!",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });

    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get(".field-email a").click();
    // Check interpolation
    cy.get("#fieldset-0-1-heading").click();
    cy.getIframeBody(".field-email_preview iframe").contains("Dear ,");
  });
  it("Check sending email with non-ASCII characters", () => {
    cy.loginEmails();
    cy.checkModelAdmin({
      modelName: "Emails",
      nameField: "subject",
      extraFields: {
        recipients: "🐉",
        content: "Dear [[full_name]],\n Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>",
      },
      suffix: "-email-subject",
      checkDelete: false,
    });

    // Wait for the task to finish
    cy.get(".field-status_display").contains("SUCCESS");
    cy.get(".field-email a").click();
    cy.get(".field-email_to").contains("ţēśţ.παράδειγμα+ó@उदाहरण例子παράδειγμαпример例.test");

    // Check placeholder interpolation in preview
    cy.get("#fieldset-0-1-heading").click();
    // Check HTML
    cy.getIframeBody(".field-email_preview iframe").contains("Dear Mr. 𝓙𝓸𝓱𝓷 🂡⚛︎ ᴛʜᴇ Łøᶑϻïŉ Ğàẕⱷņτ🎵 Ɗřăçóŋ <🐉>");
    cy.getIframeBody(".field-email_preview iframe").contains("Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>");
    // Check plaintext
    cy.get(".field-email_plaintext").contains("Dear Mr. 𝓙𝓸𝓱𝓷 🂡⚛︎ ᴛʜᴇ Łøᶑϻïŉ Ğàẕⱷņτ🎵 Ɗřăçóŋ <🐉>");
    cy.get(".field-email_plaintext").contains("Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>");
    // Check placeholder interpolation in the raw email
    cy.get("#fieldset-0-2-heading").click();
    cy.get(".field-email_source").contains("Dear Mr. 𝓙𝓸𝓱𝓷 🂡⚛︎ ᴛʜᴇ Łøᶑϻïŉ Ğàẕⱷņτ🎵 Ɗřăçóŋ <🐉>");
    cy.get(".field-email_source").contains("Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>");

    // Check the email object itself
    cy.get(".field-email a").click();
    cy.contains("View email");
    // Check HTML
    cy.getIframeBody(".field-email_preview iframe").contains("Dear [[full_name]]");
    cy.getIframeBody(".field-email_preview iframe").contains("Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>");
    // Check plaintext
    cy.get(".field-email_plaintext").contains("Dear [[full_name]]");
    cy.get(".field-email_plaintext").contains("Hëļłø! Høŵ àŗȇ ÿøû dôïńğ töđàÿ? <🎉>");
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
    cy.get("#fieldset-0-1-heading").click();
    cy.getIframeBody(".field-email_preview iframe").contains("Dear Mrs. Aria-Eclipse Titan");
    cy.get(".field-email_plaintext").contains("Dear Mrs. Aria-Eclipse Titan");
    // Check placeholder interpolation in the raw email
    cy.get("#fieldset-0-2-heading").click();
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
    cy.get("#fieldset-0-1-heading").click();
    cy.getIframeBody(".field-email_preview iframe").find("img").should("be.visible");

    // Check image is included in the raw HTML body of the email
    cy.get("#fieldset-0-2-heading").click();
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
    cy.get("#fieldset-0-1-heading").click();
    cy.get("a").contains("lorem-ipsum.txt").click();
    cy.checkFile({
      filePattern: "lorem-ipsum",
      expected: ["Lorem ipsum dolor sit amet, consectetur adipiscing elit"],
    });

    // Check attachment in the raw email
    cy.get("#fieldset-0-2-heading").click();
    cy.get(".field-email_source").contains("lorem-ipsum.txt");
    cy.get(".field-email_source").contains("Lorem ipsum dolor sit amet, consectetur adipiscing elit");
  });
  it("Check total link", () => {
    cy.loginAdmin();
    cy.performSearch({
      modelName: "Emails",
      searchValue: "placeholder",
    });
    cy.contains("1 result");
    cy.get("a").contains("30 emails").click();
    cy.contains("Select send email task");
    cy.contains("MP Nyx Spectrum");
    cy.contains("30 results");
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
