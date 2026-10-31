const form = document.querySelector("#user-search-form");
const tabs = [...form.querySelectorAll('[role="tab"]')];
const panels = [...form.querySelectorAll('[role="tabpanel"]')];
const flexibleDate = form.querySelector("#flexible-date");
const singleDate = form.querySelector("#desired-date");
const singleDateLabel = form.querySelector("#single-date-label");
const dateRangeFields = form.querySelector("#date-range-fields");
const dateRangeInputs = dateRangeFields.querySelectorAll("input");

function selectTab(tabId) {
  const selectedTab = tabs.find((tab) => tab.id === tabId);
  if (!selectedTab) {
    return;
  }

  tabs.forEach((tab) => {
    const selected = tab === selectedTab;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  panels.forEach((panel) => {
    panel.hidden = panel.id !== selectedTab.getAttribute("aria-controls");
  });
}

function updateDateFields() {
  const rangeSelected = flexibleDate.checked;
  singleDate.disabled = rangeSelected;
  singleDate.required = !rangeSelected;
  singleDateLabel.hidden = rangeSelected;
  dateRangeFields.hidden = !rangeSelected;
  dateRangeInputs.forEach((input) => {
    input.disabled = !rangeSelected;
    input.required = rangeSelected;
  });
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => selectTab(tab.id));
});

form.querySelectorAll("[data-next-tab]").forEach((button) => {
  button.addEventListener("click", () => selectTab(button.dataset.nextTab));
});

form.addEventListener("keydown", (event) => {
  if (!tabs.includes(event.target)) {
    return;
  }
  const currentIndex = tabs.indexOf(event.target);
  let nextIndex = currentIndex;
  if (event.key === "ArrowRight") {
    nextIndex = (currentIndex + 1) % tabs.length;
  } else if (event.key === "ArrowLeft") {
    nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
  } else {
    return;
  }
  event.preventDefault();
  selectTab(tabs[nextIndex].id);
  tabs[nextIndex].focus();
});

flexibleDate.addEventListener("change", updateDateFields);
updateDateFields();
selectTab(new URLSearchParams(window.location.search).has("search")
  ? "results-tab"
  : "destination-tab");
