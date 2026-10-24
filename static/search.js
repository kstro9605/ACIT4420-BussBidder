const searchForm = document.querySelector("form");
const searchButton = document.querySelector("#search-button");
const selectedRadios = new Map();
const originalRadioValues = new WeakMap();

searchForm.querySelectorAll('input[type="radio"]').forEach((radio) => {
  originalRadioValues.set(radio, radio.value);
  if (radio.checked) {
    selectedRadios.set(radio.name, radio);
  }
});

searchForm.addEventListener("click", (event) => {
  const radio = event.target;
  if (!(radio instanceof HTMLInputElement) || radio.type !== "radio") {
    return;
  }

  if (selectedRadios.get(radio.name) === radio) {
    event.preventDefault();
    radio.checked = false;
    radio.value = "None";
    selectedRadios.delete(radio.name);
    updateSearchButton();
  } else if (radio.value === "None") {
    radio.value = originalRadioValues.get(radio);
  }
});

searchForm.addEventListener("change", (event) => {
  const radio = event.target;
  if (radio instanceof HTMLInputElement && radio.type === "radio") {
    selectedRadios.set(radio.name, radio);
  }
});

function updateSearchButton() {
  const hasFilters = [...searchForm.querySelectorAll("input, select")]
    .some((field) =>
      field.type === "radio" ? field.checked : field.value.trim() !== ""
    );
  searchButton.textContent = hasFilters ? "Search trips" : "Display all trips";
}

searchForm.addEventListener("input", updateSearchButton);
searchForm.addEventListener("change", updateSearchButton);
updateSearchButton();
