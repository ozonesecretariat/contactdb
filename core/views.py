import io

import django.utils.datastructures
import openpyxl as opx
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.generic import (
    View,
    TemplateView,
    DetailView,
    DeleteView,
    UpdateView,
    ListView,
)

from core.forms import RecordUpdateForm

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from core.models import Record, RegistrationStatus
from core.tables import RecordTable
from core.filters import RecordFilter, RegistrationStatusFilter


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "core/home_page.html"


class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record


class RecordUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Record
    form_class = RecordUpdateForm

    def has_permission(self):
        return self.request.user.can_edit

    def get_success_url(self):
        return reverse("contact-detail", kwargs={"pk": self.object.pk})


class RecordDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Record

    def get_success_url(self):
        return reverse("contact-list")

    def has_permission(self):
        return self.request.user.can_edit


class ContactListView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleTableMixin, FilterView
):
    table_class = RecordTable
    queryset = Record.objects.all()
    filterset_class = RecordFilter
    paginate_by = 30

    def has_permission(self):
        return self.request.user.can_view

    def get_template_names(self):
        if self.request.htmx:
            template_name = "records_list_page_partial.html"
        else:
            template_name = "records_list_page.html"

        return template_name


class RegistrationStatusListView(LoginRequiredMixin, FilterView, ListView):
    model = RegistrationStatus
    context_object_name = "statuses"
    filterset_class = RegistrationStatusFilter
    paginate_by = 10
    ordering = ["-date"]

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/registration_status_list_partial.html"
        else:
            template_name = "core/registration_status_list.html"

        return template_name

    def get(self, request, *args, **kwargs):
        if self.request.htmx:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        page = self.request.GET.get("page", 1)
        paginator = context["paginator"]
        context["pagination_range"] = paginator.get_elided_page_range(
            number=page, on_each_side=1, on_ends=1
        )
        return context


class ImportData(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "import_export.html"

    def has_permission(self):
        return self.request.user.can_import

    def post(self, request):
        def update_field(new_value, old_value):
            return new_value if not old_value else old_value

        try:
            excel_file = request.FILES["uploaded-excel"]
            sheet_obj = opx.load_workbook(excel_file).active
        except OSError:
            messages.info(request, "File is not Excel like!")
            return redirect(reverse("import-contacts"))
        except django.utils.datastructures.MultiValueDictKeyError:
            messages.info(
                request, "Please select a file then press the 'Import' button."
            )
            return redirect(reverse("import-contacts"))

        for row in sheet_obj.iter_rows(min_row=2):
            first_name = row[8].value
            last_name = row[9].value
            address = (
                row[11].value
                + "; "
                + row[12].value
                + "; "
                + row[13].value
                + "; "
                + row[14].value
                + "; "
                + row[15].value
                + "; "
                + row[16].value
            )
            focal_point = True if row[21].value == 1 else False
            org_head = True if row[23].value == 1 else False

            try:
                if first_name and last_name:
                    contact = Record.objects.get(
                        first_name=first_name, last_name=last_name
                    )
                else:
                    contact = Record.objects.get(
                        first_name=first_name, last_name=last_name, address=address
                    )
            except Record.DoesNotExist:
                Record.objects.create(
                    country=row[0].value,
                    honorific=row[2].value,
                    primary_lang=row[3].value,
                    second_lang=row[4].value,
                    third_lang=row[5].value,
                    respectful=row[6].value,
                    title=row[7].value,
                    first_name=first_name,
                    last_name=last_name,
                    designation=row[10].value,
                    address=address,
                    phones=[row[17].value],
                    faxes=[row[18].value],
                    emails=[row[19].value],
                    focal_point=focal_point,
                    org_head=org_head,
                )
            else:
                contact.country = update_field(row[0].value, contact.country)
                contact.honorific = update_field(row[2].value, contact.honorific)
                contact.primary_lang = update_field(row[3].value, contact.primary_lang)
                contact.second_lang = update_field(row[4].value, contact.second_lang)
                contact.third_lang = update_field(row[5].value, contact.third_lang)
                contact.respectful = update_field(row[6].value, contact.respectful)
                contact.title = update_field(row[7].value, contact.title)
                contact.designation = update_field(row[10].value, contact.designation)
                contact.address = update_field(address, contact.address)
                contact.phones = update_field(list(row[17].value), contact.phones)
                contact.faxes = update_field(list(row[18].value), contact.faxes)
                contact.emails = update_field(list(row[19].value), contact.emails)
                contact.focal_point = update_field(focal_point, contact.focal_point)
                contact.org_head = update_field(org_head, contact.org_head)
                contact.save()

        messages.success(request, "Successfully imported contacts.")
        return redirect(reverse("import-contacts"))


class ExportExcel(LoginRequiredMixin, View):
    def get(self, request):
        row = 1
        wb = opx.Workbook()
        ws = wb.active
        ws.title = "Contacts"
        ws.cell(row=row, column=1, value="Country name")
        ws.cell(row=row, column=2, value="Honorific")
        ws.cell(row=row, column=3, value="Respectful")
        ws.cell(row=row, column=4, value="Title")
        ws.cell(row=row, column=5, value="First Name")
        ws.cell(row=row, column=6, value="Last Name")
        ws.cell(row=row, column=7, value="Primary language")
        ws.cell(row=row, column=8, value="Second language")
        ws.cell(row=row, column=9, value="Third language")
        ws.cell(row=row, column=10, value="Organization")
        ws.cell(row=row, column=11, value="Designation")
        ws.cell(row=row, column=12, value="Head of Org.")
        ws.cell(row=row, column=13, value="Address")
        ws.cell(row=row, column=14, value="City")
        ws.cell(row=row, column=15, value="State")
        ws.cell(row=row, column=16, value="Country")
        ws.cell(row=row, column=17, value="Postal Code")
        ws.cell(row=row, column=18, value="Telephones")
        ws.cell(row=row, column=19, value="Faxes")
        ws.cell(row=row, column=20, value="E-mails")
        ws.cell(row=row, column=21, value="Focal Point")
        ws.cell(row=row, column=22, value="In Mailing List")
        ws.cell(row=row, column=23, value="Is Using Org. Address")

        for cell in ws["1:1"]:
            cell.fill = opx.styles.PatternFill(start_color="C0C0C0", fill_type="solid")
            cell.font = opx.styles.Font(bold=True, size=10, name="Arial")
            cell.border = opx.styles.Border(
                left=opx.styles.Side(border_style="thin", color="FF000000"),
                right=opx.styles.Side(border_style="thin", color="FF000000"),
            )
            cell.alignment = opx.styles.Alignment(horizontal="center")

        qs = Record.objects.prefetch_related("organization").all().order_by("pk")
        filtered = RecordFilter(request.GET, queryset=qs).qs

        for record in filtered:
            row += 1
            ws.cell(row=row, column=1, value=record.country)
            ws.cell(row=row, column=2, value=record.honorific)
            ws.cell(row=row, column=3, value=record.respectful)
            ws.cell(row=row, column=4, value=record.title)
            ws.cell(row=row, column=5, value=record.first_name)
            ws.cell(row=row, column=6, value=record.last_name)
            ws.cell(row=row, column=7, value=record.primary_lang)
            ws.cell(row=row, column=8, value=record.second_lang)
            ws.cell(row=row, column=9, value=record.third_lang)
            ws.cell(row=row, column=10, value=str(record.organization))
            ws.cell(row=row, column=11, value=record.designation)
            ws.cell(row=row, column=12, value=record.org_head)
            ws.cell(row=row, column=13, value=record.address)
            ws.cell(row=row, column=14, value=record.city)
            ws.cell(row=row, column=15, value=record.state)
            ws.cell(row=row, column=16, value=record.country)
            ws.cell(row=row, column=17, value=record.postal_code)
            ws.cell(row=row, column=18, value=str(record.phones))
            ws.cell(row=row, column=19, value=str(record.faxes))
            ws.cell(row=row, column=20, value=str(record.emails))
            ws.cell(row=row, column=21, value=record.focal_point)
            ws.cell(row=row, column=22, value=record.is_in_mailing_list)
            ws.cell(row=row, column=23, value=record.is_use_organization_address)

        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = opx.styles.Font(size=10, name="Arial")
                if not cell.value:
                    cell.value = " "
        excel_file = io.BytesIO()
        wb.save(excel_file)
        response = HttpResponse(
            excel_file.getvalue(), content_type="application/ms-excel"
        )
        response[
            "Content-Disposition"
        ] = f"attachment; filename*=UTF-8''{'Contacts.xlsx'}"
        return response


class ExportDoc(LoginRequiredMixin, FilterView):
    queryset = Record.objects.prefetch_related("organization").all().order_by("pk")
    filterset_class = RecordFilter

    def get(self, request):
        doc = Document()
        section_header = doc.sections[0].header.paragraphs[0]
        section_header.text = "Ozone Contact DB\t"
        section_header.style.font.size = Pt(9)
        section_header.style.font.color.rgb = RGBColor(212, 212, 212)

        styles = doc.styles
        p_style = styles.add_style("FieldStyle", WD_STYLE_TYPE.PARAGRAPH)
        p_style.font.size = Pt(10)
        p_style.font.name = "Arial"
        p_style.font.italic = True
        p_style.paragraph_format.space_after = Pt(1.2)

        r_style = styles.add_style("RunStyle", WD_STYLE_TYPE.CHARACTER)
        r_style.font.size = Pt(10)
        r_style.font.name = "Arial"
        r_style.font.bold = True
        r_style.font.italic = False

        qs = Record.objects.prefetch_related("organization").all().order_by("pk")
        filtered = RecordFilter(request.GET, queryset=qs).qs
        ct = 1
        for record in filtered:
            doc.add_heading(str(ct) + ". " + record.first_name + " " + record.last_name)
            first_name = doc.add_paragraph("First name: ", style="FieldStyle")
            first_name.add_run(record.first_name, style="RunStyle")
            last_name = doc.add_paragraph("Last name: ", style="FieldStyle")
            last_name.add_run(record.last_name, style="RunStyle")
            title = doc.add_paragraph("Title: ", style="FieldStyle")
            title.add_run(record.title, style="RunStyle")
            honorific = doc.add_paragraph("Honorific: ", style="FieldStyle")
            honorific.add_run(record.honorific, style="RunStyle")
            respectful = doc.add_paragraph("Respectful: ", style="FieldStyle")
            respectful.add_run(record.respectful, style="RunStyle")
            primary_lang = doc.add_paragraph("Primary language: ", style="FieldStyle")
            primary_lang.add_run(record.primary_lang, style="RunStyle")
            second_lang = doc.add_paragraph("Second language: ", style="FieldStyle")
            second_lang.add_run(record.second_lang, style="RunStyle")
            third_lang = doc.add_paragraph("Third language: ", style="FieldStyle")
            third_lang.add_run(record.third_lang, style="RunStyle")
            org = doc.add_paragraph("Organization: ", style="FieldStyle")
            org.add_run(str(record.organization), style="RunStyle")
            org_head = doc.add_paragraph("Head of organization: ", style="FieldStyle")
            org_head.add_run(str(record.org_head), style="RunStyle")
            affiliation = doc.add_paragraph("Affiliation: ", style="FieldStyle")
            affiliation.add_run(record.affiliation, style="RunStyle")
            designation = doc.add_paragraph("Designation: ", style="FieldStyle")
            designation.add_run(record.designation, style="RunStyle")
            department = doc.add_paragraph("Department: ", style="FieldStyle")
            department.add_run(record.department, style="RunStyle")
            phones = doc.add_paragraph("Telephones: ", style="FieldStyle")
            phones.add_run(str(record.phones), style="RunStyle")
            faxes = doc.add_paragraph("Faxes: ", style="FieldStyle")
            faxes.add_run(str(record.faxes), style="RunStyle")
            emails = doc.add_paragraph("E-mails: ", style="FieldStyle")
            emails.add_run(str(record.emails), style="RunStyle")
            notes = doc.add_paragraph("Notes: ", style="FieldStyle")
            notes.add_run(record.notes, style="RunStyle")
            focal_point = doc.add_paragraph("Focal point: ", style="FieldStyle")
            focal_point.add_run(str(record.focal_point), style="RunStyle")
            mailing_list = doc.add_paragraph("Is in mailing list: ", style="FieldStyle")
            mailing_list.add_run(str(record.is_in_mailing_list), style="RunStyle")
            org_addr = doc.add_paragraph(
                "Is using organization address: ", style="FieldStyle"
            )
            org_addr.add_run(str(record.is_use_organization_address), style="RunStyle")
            addr = doc.add_paragraph("Address: ", style="FieldStyle")
            addr.add_run(record.address, style="RunStyle")
            city = doc.add_paragraph("City: ", style="FieldStyle")
            city.add_run(record.city, style="RunStyle")
            state = doc.add_paragraph("State: ", style="FieldStyle")
            state.add_run(record.state, style="RunStyle")
            country = doc.add_paragraph("Country: ", style="FieldStyle")
            country.add_run(record.country, style="RunStyle")
            postal_code = doc.add_paragraph("Postal code: ", style="FieldStyle")
            postal_code.add_run(record.postal_code, style="RunStyle")
            birth_date = doc.add_paragraph("Birth date: ", style="FieldStyle")
            birth_date.add_run(str(record.birth_date), style="RunStyle")
            doc.add_page_break()
            ct += 1

        doc_file = io.BytesIO()
        doc.save(doc_file)
        response = HttpResponse(doc_file.getvalue(), content_type="application/ms-word")
        response[
            "Content-Disposition"
        ] = f"attachment; filename*=UTF-8''{'Contacts.docx'}"
        return response
