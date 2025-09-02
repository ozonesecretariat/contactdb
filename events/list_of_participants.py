import io
import itertools
from enum import Enum
from typing import Callable, Iterable

from django.utils import timezone
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

from events.exports.docx_utils import (
    add_page_number,
    insert_hr,
    set_cell,
    set_repeat_table_header,
    set_table_border,
)
from events.models import Registration


class Section(Enum):
    PARTIES = "Parties"
    ASS_PANELS = "Assessment Panels"
    OBSERVERS = "Observers"
    SECRETARIAT = "Ozone Secretariat"


ZERO = Inches(0)
USABLE_WIDTH = Inches(8)
INDEX_COL_WIDTH = Inches(0.5)
CONTACT_COL_WIDTH = Inches(3.45)

TOP_MARGIN = Inches(0.25)
BOTTOM_MARGIN = Inches(0.25)
LEFT_MARGIN = Inches(0.25)
RIGHT_MARGIN = Inches(0.25)


class ListOfParticipants:
    def __init__(self, event):
        self.doc = Document()
        self.event = event
        self.all_registrations = list(
            self.event.registrations.filter(status=Registration.Status.REGISTERED)
            .prefetch_related(
                "contact",
                "organization",
                "organization__organization_type",
                "organization__country",
                "organization__government",
                "organization__government__region",
                "organization__government__subregion",
            )
            .order_by("organization__government__name", "organization__name")
        )
        self.global_index = 0

    def export_docx(self):
        self.init_docx()
        self.get_content()
        return self.save_docx()

    def init_docx(self):
        self.doc.settings.odd_and_even_pages_header_footer = True

        styles = self.doc.styles
        styles["Normal"].font.name = "Arial"

        header_style = styles.add_style("LOP Header", WD_STYLE_TYPE.PARAGRAPH)
        header_style.font.name = "Arial"
        header_style.font.bold = False
        header_style.font.italic = True
        header_style.font.size = Pt(9)
        header_style.paragraph_format.space_after = Pt(0)
        header_style.paragraph_format.space_before = Pt(0)

        header_style = styles.add_style("LOP Header Title", WD_STYLE_TYPE.PARAGRAPH)
        header_style.font.name = "Arial"
        header_style.font.bold = True
        header_style.font.size = Pt(16)
        header_style.paragraph_format.keep_together = True
        header_style.paragraph_format.keep_with_next = True
        header_style.paragraph_format.space_after = Pt(0)
        header_style.paragraph_format.space_before = Pt(0)

        table_style = styles.add_style("LOP Table", WD_STYLE_TYPE.TABLE)
        table_style.font.name = "Arial"
        table_style.font.size = Pt(11)

        space_style = styles.add_style("LOP Table Space", WD_STYLE_TYPE.PARAGRAPH)
        space_style.paragraph_format.space_after = Pt(0)
        space_style.paragraph_format.space_before = Pt(0)
        space_style.font.size = Pt(4)

        group_style = styles.add_style("LOP L1 Group", WD_STYLE_TYPE.PARAGRAPH)
        group_style.font.name = "Arial"
        group_style.font.size = Pt(14)
        group_style.font.bold = True
        group_style.paragraph_format.keep_together = True
        group_style.paragraph_format.keep_with_next = True

        group_style = styles.add_style("LOP L2 Group", WD_STYLE_TYPE.PARAGRAPH)
        group_style.font.name = "Arial"
        group_style.font.bold = True
        group_style.font.underline = True
        group_style.paragraph_format.keep_together = True
        group_style.paragraph_format.keep_with_next = True

        footer_style = styles.add_style("LOP Footer", WD_STYLE_TYPE.PARAGRAPH)
        footer_style.font.name = "Arial"
        footer_style.font.size = Pt(9)
        footer_style.paragraph_format.space_after = Pt(0)
        footer_style.paragraph_format.space_before = Pt(0)

        self.doc.sections[0].different_first_page_header_footer = True
        self.set_footer(self.doc.sections[0].footer)
        self.set_footer(self.doc.sections[0].even_page_footer)

    def set_footer(self, footer):
        footer.paragraphs[0].clear()

        insert_hr(footer.paragraphs[0])
        table = footer.add_table(1, 2, USABLE_WIDTH)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.left_indent = ZERO
        set_table_border(table, size=0, border_type="none")

        p = table.cell(0, 0).paragraphs[0]
        p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        p.style = "LOP Footer"
        p.add_run(str(timezone.now().date()))

        p = table.cell(0, 1).paragraphs[0]
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        p.style = "LOP Footer"
        add_page_number(p.add_run())

    def get_content(self):
        self.cover_page()

        sections = {
            Section.PARTIES: [],
            Section.ASS_PANELS: [],
            Section.OBSERVERS: [],
            Section.SECRETARIAT: [],
        }

        for r in self.all_registrations:
            if r.is_gov and r.usable_government:
                sections[Section.PARTIES].append(r)
            elif r.is_ass_panel:
                sections[Section.ASS_PANELS].append(r)
            elif r.is_secretariat:
                sections[Section.SECRETARIAT].append(r)
            else:
                sections[Section.OBSERVERS].append(r)

        self.configure_section(self.doc.add_section(), Section.PARTIES.value)
        self.grouped_participants(
            sections[Section.PARTIES],
            lambda r: r.usable_government.name,
        )

        self.configure_section(self.doc.add_section(), Section.ASS_PANELS.value)
        self.grouped_participants(
            sections[Section.ASS_PANELS],
            lambda r: r.usable_organization_name,
        )

        self.configure_section(self.doc.add_section(), Section.OBSERVERS.value)
        self.grouped_participants(
            sections[Section.OBSERVERS],
            lambda r: r.usable_organization_name or "Unknown",
            lambda r: r.usable_organization_type_description or "Unknown",
        )

        self.configure_section(self.doc.add_section(), Section.SECRETARIAT.value)
        self.grouped_participants(
            sections[Section.SECRETARIAT],
            lambda r: r.usable_organization_name,
        )

    def configure_section(self, section, header_text):
        section.different_first_page_header_footer = False
        section.top_margin = TOP_MARGIN
        section.bottom_margin = BOTTOM_MARGIN
        section.left_margin = LEFT_MARGIN
        section.right_margin = RIGHT_MARGIN

        # Set the layout to two columns
        cols = section._sectPr.xpath("./w:cols")[0]
        cols.set(qn("w:num"), "2")
        cols.set(qn("w:space"), "144")

        self.set_section_header(
            section.header, header_text, WD_PARAGRAPH_ALIGNMENT.RIGHT
        )
        self.set_section_header(
            section.even_page_header, header_text, WD_PARAGRAPH_ALIGNMENT.LEFT
        )

    def set_section_header(self, header, header_text, alignment):
        header.is_linked_to_previous = False
        p = header.paragraphs[0]
        p.alignment = alignment
        p.style = "LOP Header"
        p.text = "UNEP///"
        insert_hr(p)

        table = header.add_table(1, 1, USABLE_WIDTH)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.left_indent = ZERO
        set_cell(
            table=table,
            row=0,
            col=0,
            text=header_text,
            style="LOP Header Title",
            align=WD_PARAGRAPH_ALIGNMENT.CENTER,
            v_align=WD_CELL_VERTICAL_ALIGNMENT.CENTER,
            bg_color="#e0e0e0",
        )
        header.add_paragraph("", style="LOP Table Space")

    def cover_page(self):
        self.doc.add_heading("List of Participants", level=1)
        self.doc.add_paragraph("")
        self.doc.add_heading(self.event.title, level=2)

    def grouped_participants(
        self,
        registrations: Iterable[Registration],
        key1: Callable[[Registration], str],
        key2: Callable[[Registration], str] = None,
    ):
        registrations = sorted(registrations, key=lambda r: r.contact.full_name)
        registrations = sorted(registrations, key=key1)
        if key2:
            registrations = sorted(registrations, key=key2)
        else:
            key2 = lambda x: ""  # noqa: E731

        for l1_group_name, l1_group_items in itertools.groupby(registrations, key=key2):
            if l1_group_name:
                self.doc.add_paragraph(l1_group_name, style="LOP L1 Group")

            for l2_group_name, l2_group_items in itertools.groupby(
                l1_group_items, key=key1
            ):
                items = list(l2_group_items)

                table = self.doc.add_table(len(items) + 1, 2, style="LOP Table")
                table.alignment = WD_TABLE_ALIGNMENT.LEFT
                table.left_indent = ZERO
                table.allow_autofit = False
                table.columns[0].width = INDEX_COL_WIDTH
                table.columns[1].width = CONTACT_COL_WIDTH
                set_table_border(table, size=0, border_type="none")

                header_row = table.rows[0]
                header_row.cells[0].merge(header_row.cells[1])
                set_repeat_table_header(header_row)

                header_p = table.cell(0, 0).paragraphs[0]
                header_p.style = "LOP L2 Group"
                header_p.add_run(l2_group_name)

                for row_index, item in enumerate(items, start=1):
                    self.global_index += 1

                    # Don't allow rows to be split across pages (or columns
                    row = table.rows[row_index]
                    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

                    # Set the global index, tracked across sections
                    cell = row.cells[0]
                    cell.width = INDEX_COL_WIDTH
                    p = cell.paragraphs[0]
                    p.add_run(f"{self.global_index}.").bold = True
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    p.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP

                    # Set the contact information
                    cell = row.cells[1]
                    cell.width = CONTACT_COL_WIDTH
                    p = row.cells[1].paragraphs[0]
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    p.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                    self.contact_list_item(p, item)

                self.doc.add_paragraph("", style="LOP Table Space")

    def contact_list_item(self, p: Paragraph, reg: Registration):
        p.paragraph_format.keep_together = True
        p.add_run(reg.contact.full_name.strip() or "-").bold = True

        organization = reg.organization or reg.contact.organization
        address_obj = (
            organization if reg.contact.is_use_organization_address else reg.contact
        )

        possible_values = [
            reg.designation or reg.contact.designation,
            reg.department or reg.contact.department,
            organization and organization.name,
            address_obj.address,
            ", ".join(
                filter(
                    lambda x: x,
                    [
                        address_obj.city.strip(),
                        address_obj.state.strip(),
                        address_obj.postal_code.strip(),
                    ],
                )
            ),
            address_obj.country and address_obj.country.name,
        ]

        values = []
        for value in possible_values:
            if value := (value or "").strip():
                values.append(value)

        if values:
            p.add_run("\n" + "\n".join(values))

        emails = [e.strip() for e in reg.contact.emails if e.strip()]
        if emails:
            p.add_run("\nEmail: " + ", ".join(emails))

    def save_docx(self):
        doc_file = io.BytesIO()
        doc_file.name = f"{self.event.code}-LOP.docx"
        self.doc.save(doc_file)
        doc_file.seek(0)
        return doc_file
