describe("Check", () => {
  it("Check model admin", () => {
    cy.loginEdit();
    cy.checkModelAdmin({
      modelName: "Events",
      nameField: "code",
      extraFields: {
        title: "test event",
        start_date_0: "2024-04-18",
        start_date_1: "00:00:00",
        end_date_0: "2024-04-20",
        end_date_1: "00:00:00",
        venue_country: "Romania",
        venue_city: "online",
        dates: "18-20 April 2024",
      },
    });
  });
});
