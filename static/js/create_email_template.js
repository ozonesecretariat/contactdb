function openCreateTemplateDialog(detailPage = false) {
  var dialog = document.getElementById("createEmailTemplate");

  $.when(htmx.ajax("GET", dialog.dataset.url, "div.create-email-template")).done(function () {
    if (detailPage) {
      data = document.getElementById("email-content").innerHTML;
    } else {
      data = CKEDITOR.instances["id_content"].getData();
    }
    $("#id_html_content").val(data);
  });
  dialog.showModal();
}

function closeCreateTemplateDialog() {
  var dialog = document.getElementById("createEmailTemplate");
  dialog.close();
}
