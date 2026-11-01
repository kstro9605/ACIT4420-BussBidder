document.querySelectorAll(".booking-form").forEach((form) => {
  const ticketInput = form.querySelector("[data-ticket-input]");
  const passengerList = form.querySelector("[data-passenger-list]");
  const ticketCount = form.querySelector("[data-ticket-count]");
  const bookButton = form.querySelector("[data-book-button]");
  const totalOutput = form.querySelector("[data-total]");
  const availableSeats = Number(form.dataset.seatsAvailable);
  const price = Number(form.dataset.price);

  function updateBookingForm() {
    const tickets = Number(ticketInput.value);
    const validTicketCount = Number.isInteger(tickets)
      && tickets >= 1
      && tickets <= availableSeats;

    passengerList.querySelectorAll("label").forEach((label, index) => {
      if (index >= tickets) {
        label.remove();
      }
    });

    const currentNames = passengerList.querySelectorAll("input[name='passenger_names']");
    for (let index = currentNames.length; index < (validTicketCount ? tickets : 0); index += 1) {
      const label = document.createElement("label");
      const input = document.createElement("input");
      const passengerNumber = index + 1;
      label.htmlFor = `${ticketInput.id}-passenger-${passengerNumber}`;
      label.textContent = `Passenger ${passengerNumber} name`;
      input.id = label.htmlFor;
      input.name = "passenger_names";
      input.type = "text";
      input.autocomplete = "name";
      input.required = true;
      label.append(input);
      passengerList.append(label);
    }

    ticketCount.value = validTicketCount ? String(tickets) : "0";
    totalOutput.textContent = validTicketCount
      ? `Total: €${(price * tickets).toFixed(2)}`
      : "Enter a ticket count within the available seats.";
    bookButton.disabled = !validTicketCount
      || passengerList.querySelectorAll("input[name='passenger_names']")
        .length !== tickets
      || [...passengerList.querySelectorAll("input[required]")]
        .some((input) => !input.value.trim());
  }

  ticketInput.addEventListener("input", updateBookingForm);
  passengerList.addEventListener("input", updateBookingForm);
  form.addEventListener("submit", (event) => {
    updateBookingForm();
    if (bookButton.disabled || !form.reportValidity()) {
      event.preventDefault();
    }
  });

  updateBookingForm();
});
