const priorityForm = document.querySelector("#priority-form");

if (priorityForm) {
  const rows = [...priorityForm.querySelectorAll("[data-priority-row]")];
  const totalOutput = priorityForm.querySelector("#weight-total");
  const progress = priorityForm.querySelector("#weight-progress");

  function updatePriorityControls(changedWeight = null) {
    rows.forEach((row) => {
      const enabled = row.querySelector('input[name="priority_type"]').checked;
      const weight = row.querySelector("[data-weight]");
      const qualifierToggle = row.querySelector("[data-qualifier-toggle]");
      const qualifierFields = row.querySelector("[data-qualifier-fields]");

      weight.disabled = !enabled;
      if (qualifierToggle) {
        qualifierToggle.disabled = !enabled;
        qualifierFields.hidden = !enabled || !qualifierToggle.checked;
        row.querySelectorAll("[data-qualifier-input]").forEach((input) => {
          input.disabled = !enabled || !qualifierToggle.checked;
        });
      }
    });

    if (changedWeight) {
      const otherTotal = rows.reduce((sum, row) => {
        const enabled = row.querySelector('input[name="priority_type"]').checked;
        const weight = row.querySelector("[data-weight]");
        return sum + (enabled && weight !== changedWeight ? Number(weight.value) : 0);
      }, 0);
      changedWeight.value = Math.min(Number(changedWeight.value), 100 - otherTotal);
    }

    let total = rows.reduce((sum, row) => {
      const enabled = row.querySelector('input[name="priority_type"]').checked;
      const weight = row.querySelector("[data-weight]");
      const output = row.querySelector("[data-weight-output]");
      output.value = weight.value;
      output.textContent = weight.value;
      return sum + (enabled ? Number(weight.value) : 0);
    }, 0);

    rows.forEach((row) => {
      const enabled = row.querySelector('input[name="priority_type"]').checked;
      const weight = row.querySelector("[data-weight]");
      const otherTotal = total - (enabled ? Number(weight.value) : 0);
      weight.max = Math.max(0, 100 - otherTotal);
      if (enabled && Number(weight.value) > Number(weight.max)) {
        total -= Number(weight.value) - Number(weight.max);
        weight.value = weight.max;
        const output = row.querySelector("[data-weight-output]");
        output.value = weight.value;
        output.textContent = weight.value;
      }
    });

    total = rows.reduce((sum, row) => {
      const enabled = row.querySelector('input[name="priority_type"]').checked;
      return sum + (enabled ? Number(row.querySelector("[data-weight]").value) : 0);
    }, 0);
    totalOutput.value = total;
    totalOutput.textContent = total;
    progress.value = total;
  }

  rows.forEach((row) => {
    row.querySelector('input[name="priority_type"]').addEventListener("change", () => {
      updatePriorityControls();
    });
    row.querySelector("[data-weight]").addEventListener("input", (event) => {
      updatePriorityControls(event.currentTarget);
    });
    const qualifierToggle = row.querySelector("[data-qualifier-toggle]");
    if (qualifierToggle) {
      qualifierToggle.addEventListener("change", () => updatePriorityControls());
    }
  });

  updatePriorityControls();
}
