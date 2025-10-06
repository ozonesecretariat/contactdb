function addArrayWidget(fieldEl, value = null) {
  const parentNode = fieldEl.querySelector(".vArrayWidgetList");
  const template = fieldEl.querySelector(".widgetTemplate .vArrayWidget");
  const newWidget = template.cloneNode(true);

  if (value) {
    newWidget.querySelector("input").value = value;
  }

  parentNode.append(newWidget);
  return newWidget;
}

function handleArrayFieldEvent(event) {
  const actionTarget = event.target.closest("[data-array-action]");
  if (!actionTarget) {
    return;
  }

  let widgetTarget = actionTarget.closest(".vArrayWidget");

  switch (actionTarget.dataset.arrayAction) {
    case "add":
      widgetTarget = addArrayWidget(actionTarget.closest(".vArrayField"));
      break;
    case "movedown":
      widgetTarget.nextElementSibling?.after(widgetTarget);
      break;
    case "moveup":
      widgetTarget.previousElementSibling?.before(widgetTarget);
      break;
    case "remove":
      widgetTarget.remove();
      break;
    default:
      return;
  }

  widgetTarget.querySelector("input").focus();
}

document.addEventListener("DOMContentLoaded", () => {
  for (const el of document.querySelectorAll(".vArrayField")) {
    el.addEventListener("mouseup", handleArrayFieldEvent);
  }
});

/**
 * Check if two arrays are equal
 *
 * @param a1 {Array}
 * @param a2 {Array}
 * @return {Boolean}
 */
function arrayEquals(a1, a2) {
  if (!a1 || !a2 || a1.length !== a2.length) {
    return false;
  }
  for (let i = 0; i < a1.length; i += 1) {
    if (a1[i] !== a2[i]) {
      return false;
    }
  }
  return true;
}

function checkForDifferences() {
  for (const el of document.querySelectorAll("fieldset.compare .form-row")) {
    const newValue = getNewValue(el);

    let currentInput = null;
    let different = false;

    if ((currentInput = el.querySelector(".vArrayWidgetList"))) {
      const currentArray = Array.from(currentInput.querySelectorAll("input"))
        .map((item) => item.value.trim())
        .filter((val) => Boolean(val));
      different = !arrayEquals(currentArray, newValue.value);
    } else if ((currentInput = el.querySelector("select"))) {
      // For select inputs that are not foreign keys, there is no
      // primary key (pk), so compare their values directly.
      const compareTo = newValue.pk || newValue.value;
      different = currentInput.value !== compareTo;
    } else if ((currentInput = el.querySelector("input[type=checkbox]"))) {
      different = (currentInput.checked ? "True" : "False") !== newValue.value;
    } else if ((currentInput = el.querySelector("input, textarea"))) {
      different = currentInput.value.trim() !== newValue.value;
    }

    if (different && newValue.value) {
      el.classList.add("different");
    } else {
      el.classList.remove("different");
    }
  }
}

function copyFromNew(event) {
  event.preventDefault();
  event.stopPropagation();

  const el = event.target.closest(".form-row");
  const newValue = getNewValue(el);

  if (!newValue.value) {
    return;
  }

  let input = null;

  if ((input = el.querySelector(".vArrayField"))) {
    for (const existingEl of input.querySelectorAll(".vArrayWidgetList .vArrayWidget")) {
      existingEl.remove();
    }

    for (const value of newValue.value || [""]) {
      addArrayWidget(input, value);
    }
  } else if ((input = el.querySelector("select"))) {
    const option = new Option(newValue.value, newValue.pk, true, true);
    input.append(option);
    input.dispatchEvent(new Event("change"));
    input.dispatchEvent(new Event("select2:select"));
  } else if ((input = el.querySelector("input[type=checkbox]"))) {
    input.checked = newValue.value.toLowerCase() === "true";
  } else if ((input = el.querySelector("input, textarea"))) {
    input.value = newValue.value;
  }

  checkForDifferences();
}

function getNewValue(el) {
  const newValueEl = el.querySelector(".fieldBox:not(.field-copy_widget) .readonly");
  if (!newValueEl) {
    return {};
  }
  const pk = newValueEl.querySelector("[data-pk]")?.dataset.pk.trim();

  let value = null;
  const listElement = newValueEl.querySelector("ul");
  if (listElement) {
    value = Array.from(listElement.querySelectorAll("li")).map((listEl) => listEl.innerText.trim());
    if (value.length === 0) {
      value = null;
    }
  } else {
    value = newValueEl.innerText.trim();
    if (value === "-") {
      value = null;
    }
  }

  return { pk, value };
}

document.addEventListener("DOMContentLoaded", () => {
  const $ = window.django.jQuery;
  $("[data-choice-select2=true]").select2();

  checkForDifferences();
  for (const el of document.querySelectorAll("fieldset.compare .form-row")) {
    el.querySelector(".copy-button")?.addEventListener("click", copyFromNew);
    for (const elInput of el.querySelectorAll("input, select, textarea")) {
      elInput.addEventListener("input", checkForDifferences);
    }
  }
});
