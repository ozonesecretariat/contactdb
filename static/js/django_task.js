/* eslint-disable camelcase */

// Rearranged code from the original django_task.js to fix getCookie issue.

function initDjangoTask($) {
  let update_tasks_timer = null;

  function getCookie(name) {
    const cookies = {};
    for (const pair of document.cookie.split(";")) {
      const [key, value] = pair.split("=");
      cookies[key.trim()] = value.trim();
    }
    return cookies[name];
  }

  function view_log_text(event) {
    const url = $(event.target).attr("href");
    $.ajax({
      success(data) {
        // eslint-disable-next-line no-alert
        alert(data);
      },
      type: "GET",
      url,
    });
    return false;
  }

  function update_task_row(item, selector) {
    const row = $(`${selector} .task_status[data-task-id="${item.id}"]`).closest("tr");
    if (row.length) {
      $(row).find(".field-started_on_display").html(item.started_on_display);
      $(row).find(".field-completed_on_display").html(item.completed_on_display);
      $(row).find(".field-duration_display").html(item.duration_display);
      $(row).find(".field-status_display").html(item.status_display);
      $(row).find(".field-progress_display").html(item.progress_display);
      $(row).find(".field-log_link_display").html(item.log_link_display);
      for (const [key, value] of Object.entries(item.extra_fields)) {
        $(row).find(`.field-${key}`).html(value);
      }
      $(row).find(".field-log_link_display a.logtext").on("click", view_log_text);
    }
  }

  function update_tasks(autorepeat_interval, selector = "#result_list") {
    // clear one-shot timer
    if (update_tasks_timer !== null) {
      clearTimeout(update_tasks_timer);
      update_tasks_timer = null;
    }

    // Collect incomplete tasks
    const incomplete_tasks = [];
    $(`${selector} .task_status[data-task-complete="0"]`).each((index, item) => {
      incomplete_tasks.push({
        id: $(item).data("task-id"),
        model: $(item).data("task-model"),
      });
    });

    if (incomplete_tasks.length > 0) {
      $.ajax({
        cache: false,
        crossDomain: true,
        data: JSON.stringify(incomplete_tasks),
        dataType: "json",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        type: "post",
        url: "/django_task/info/",
      })
        .done((data) => {
          let repeat = false;
          $.each(data, (index, item) => {
            if (!item.completed) {
              repeat = true;
            }
            update_task_row(item, selector);
          });
          if (repeat) {
            // re-arm timer
            if (autorepeat_interval > 0) {
              setTimeout(() => {
                update_tasks(autorepeat_interval, selector);
              }, autorepeat_interval);
            }
          }
        })
        .fail(() => {
          // re-arm timer
          if (autorepeat_interval > 0) {
            setTimeout(() => {
              update_tasks(autorepeat_interval, selector);
            }, autorepeat_interval);
          }
        });
    }
  }

  const body = $("body");
  if (body.hasClass("change-list") || body.hasClass("grp-change-list")) {
    $(".field-log_link_display a.logtext").on("click", view_log_text);
    update_tasks(1000);
  }
  if (body.hasClass("change-form") || body.hasClass("grp-change-form")) {
    // hide "save and continue" button from the submit row
    $('.submit-row button[name="_continue"]').hide();
  }

  return {
    update_tasks,
  };
}

window.addEventListener("load", () => {
  window.DjangoTask = initDjangoTask(window.$ || window.jQuery || window.django.jQuery);
});
