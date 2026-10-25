const priorityForm = document.querySelector("#priority-form");

if (priorityForm) {
  const dropzone = priorityForm.querySelector("#priority-dropzone");
  const options = [...priorityForm.querySelectorAll("[data-priority-option]")];
  const rows = [...priorityForm.querySelectorAll("[data-priority-row]")];
  const totalOutput = priorityForm.querySelector("#weight-total");
  const progress = priorityForm.querySelector("#weight-progress");
  const chart = priorityForm.querySelector("#priority-chart");
  const emptyState = priorityForm.querySelector("[data-empty-state]");
  const chartColors = [
    "#176b56",
    "#4d9b82",
    "#e5a94b",
    "#5b83b5",
    "#bd6b58",
    "#8a70a5",
    "#6e8790",
    "#c57d9b",
    "#9b9b55",
  ];

  function activeRows() {
    return rows.filter((row) => !row.hidden);
  }

  function rebalanceWeights() {
    const active = activeRows();
    if (!active.length) {
      return;
    }
    const baseWeight = Math.floor(100 / active.length);
    active.forEach((row, index) => {
      const weight = row.querySelector("[data-weight-number]");
      const value = index === active.length - 1
        ? 100 - baseWeight * (active.length - 1)
        : baseWeight;
      weight.value = value;
      row.querySelector("[data-weight-range]").value = value;
    });
  }

  function updatePriorityControls(changedWeight = null) {
    const active = activeRows();

    rows.forEach((row) => {
      const enabled = !row.hidden;
      const priorityInput = row.querySelector("[data-priority-input]");
      const range = row.querySelector("[data-weight-range]");
      const number = row.querySelector("[data-weight-number]");
      const qualifierToggle = row.querySelector("[data-qualifier-toggle]");
      const qualifierFields = row.querySelector("[data-qualifier-fields]");
      const requiresQualifier = qualifierToggle?.hasAttribute(
        "data-required-qualifier",
      ) ?? false;

      priorityInput.disabled = !enabled;
      range.disabled = !enabled;
      number.disabled = !enabled;
      if (qualifierToggle) {
        if (requiresQualifier) {
          qualifierToggle.checked = true;
        } else {
          qualifierToggle.disabled = !enabled;
        }
        const showQualifier = enabled && (requiresQualifier || qualifierToggle.checked);
        qualifierFields.hidden = !showQualifier;
        row.querySelectorAll("[data-qualifier-input]").forEach((input) => {
          input.disabled = !showQualifier;
        });
      }
    });

    if (changedWeight) {
      const row = changedWeight.closest("[data-priority-row]");
      const range = row.querySelector("[data-weight-range]");
      const otherTotal = active.reduce((sum, activeRow) => {
        if (activeRow === row) {
          return sum;
        }
        return sum + Number(activeRow.querySelector("[data-weight-number]").value);
      }, 0);
      const maximum = Math.max(0, 100 - otherTotal);
      changedWeight.value = Math.min(
        Math.max(0, Number(changedWeight.value) || 0),
        maximum,
      );
      range.value = changedWeight.value;
    }

    let total = 0;
    active.forEach((row) => {
      const range = row.querySelector("[data-weight-range]");
      const number = row.querySelector("[data-weight-number]");
      const otherTotal = active.reduce((sum, otherRow) => (
        otherRow === row
          ? sum
          : sum + Number(otherRow.querySelector("[data-weight-number]").value)
      ), 0);
      const maximum = Math.max(0, 100 - otherTotal);
      range.max = maximum;
      number.max = maximum;
      const weight = Math.min(Number(number.value) || 0, maximum);
      number.value = weight;
      range.value = weight;
      total += weight;
    });

    totalOutput.value = total;
    totalOutput.textContent = total;
    progress.value = total;
    emptyState.hidden = active.length > 0;

    let degrees = 0;
    const segments = [];
    active.forEach((row, index) => {
      const weight = Number(row.querySelector("[data-weight-number]").value);
      if (weight <= 0) {
        return;
      }
      const endDegrees = degrees + weight * 3.6;
      segments.push(
        `${chartColors[index % chartColors.length]} ${degrees}deg ${endDegrees}deg`,
      );
      degrees = endDegrees;
    });
    if (degrees < 360) {
      segments.push(`transparent ${degrees}deg 360deg`);
    }
    chart.style.setProperty(
      "--priority-chart-segments",
      segments.length ? segments.join(", ") : "transparent 0deg 360deg",
    );
    chart.setAttribute(
      "aria-label",
      `Priority weights total ${total} out of 100 points`,
    );
  }

  function addPriority(name) {
    const option = options.find((item) => item.dataset.priorityName === name);
    const row = rows.find((item) => item.dataset.priorityName === name);
    if (!option || !row || !row.hidden) {
      return;
    }
    row.hidden = false;
    option.hidden = true;
    rebalanceWeights();
    updatePriorityControls();
  }

  function removePriority(name) {
    const option = options.find((item) => item.dataset.priorityName === name);
    const row = rows.find((item) => item.dataset.priorityName === name);
    if (!option || !row || row.hidden) {
      return;
    }
    row.hidden = true;
    option.hidden = false;
    rebalanceWeights();
    updatePriorityControls();
  }

  options.forEach((option) => {
    option.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", option.dataset.priorityName);
      event.dataTransfer.effectAllowed = "copy";
    });
    option.querySelector("[data-add-priority]").addEventListener("click", () => {
      addPriority(option.dataset.priorityName);
    });
  });

  [chart, dropzone].forEach((target) => {
    target.addEventListener("dragover", (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
      target.classList.add("is-drop-target");
    });
    target.addEventListener("dragleave", (event) => {
      if (!target.contains(event.relatedTarget)) {
        target.classList.remove("is-drop-target");
      }
    });
    target.addEventListener("drop", (event) => {
      event.preventDefault();
      target.classList.remove("is-drop-target");
      addPriority(event.dataTransfer.getData("text/plain"));
    });
  });

  rows.forEach((row) => {
    row.querySelector("[data-remove-priority]").addEventListener("click", () => {
      removePriority(row.dataset.priorityName);
    });
    row.querySelector("[data-weight-range]").addEventListener("input", (event) => {
      const number = row.querySelector("[data-weight-number]");
      number.value = event.currentTarget.value;
      updatePriorityControls(number);
    });
    row.querySelector("[data-weight-number]").addEventListener("input", (event) => {
      updatePriorityControls(event.currentTarget);
    });
    const qualifierToggle = row.querySelector("[data-qualifier-toggle]");
    if (qualifierToggle && !qualifierToggle.disabled) {
      qualifierToggle.addEventListener("change", () => updatePriorityControls());
    }
  });

  updatePriorityControls();
}
