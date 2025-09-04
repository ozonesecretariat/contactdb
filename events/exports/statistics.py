import io
from collections import Counter
from decimal import Decimal
from typing import Collection

from django.utils import timezone
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Cm, Pt, RGBColor

from core.models import OrganizationType, Region
from events.exports.docx_utils import set_cell, set_table_border, set_table_caption
from events.models import Event, Registration


class PreMeetingStatistics:
    def __init__(self, event: Event):
        self.doc = Document()
        self.event = event
        self.regions = list(
            Region.objects.all()
            .prefetch_related("countries", "countries__subregion")
            .order_by("-name")
        )
        self.accredited_registrations = []
        for r in self.get_query():
            try:
                if r.usable_organization.organization_type.hide_in_statistics:
                    continue
            except AttributeError:
                pass
            self.accredited_registrations.append(r)

        self.accredited_gov_registrations = [
            registration
            for registration in self.accredited_registrations
            if registration.is_gov
        ]
        self.accredited_gov_parties = {
            registration.usable_government
            for registration in self.accredited_gov_registrations
        }

    def get_query(self):
        return self.event.registrations.filter(
            status=Registration.Status.ACCREDITED
        ).prefetch_related(
            "organization",
            "organization__organization_type",
            "organization__government",
            "organization__government__region",
            "organization__government__subregion",
            "contact",
            "contact__organization",
            "contact__organization__organization_type",
            "contact__organization__government",
            "contact__organization__government__region",
            "contact__organization__government__subregion",
        )

    def export_docx(self):
        self.init_docx()
        self.get_content()
        return self.save_docx()

    def init_docx(self):
        styles = self.doc.styles

        styles["Normal"].font.name = "Times New Roman"

        table_style = styles.add_style("Stat Table", WD_STYLE_TYPE.TABLE)
        table_style.font.size = Pt(11)
        table_style.font.name = "Times New Roman"
        table_style.paragraph_format.keep_together = True
        table_style.paragraph_format.keep_with_next = True
        table_style.paragraph_format.space_after = Pt(5)
        table_style.paragraph_format.space_before = Pt(5)

        th_style = styles.add_style("Table Header", WD_STYLE_TYPE.PARAGRAPH)
        th_style.font.bold = True
        th_style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

        td_style = styles.add_style("Table Data", WD_STYLE_TYPE.PARAGRAPH)
        td_style.font.bold = False

        tf_style = styles.add_style("Table Footer", WD_STYLE_TYPE.PARAGRAPH)
        tf_style.font.bold = True

        for section in self.doc.sections:
            header = section.header.paragraphs[0]
            header.text = str(self.event)
            header.style.font.size = Pt(9)
            header.style.font.color.rgb = RGBColor(45, 45, 45)
            header.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

            footer = section.footer.paragraphs[0]
            footer.text = "Date: " + timezone.now().strftime(" %Y-%m-%d %H:%M %Z")
            footer.style.font.size = Pt(9)
            footer.style.font.color.rgb = RGBColor(45, 45, 45)

            section.top_margin = Cm(0)
            section.bottom_margin = Cm(0)
            section.left_margin = Cm(1)
            section.right_margin = Cm(1)

    def _max_cols(self, obj: Collection[Collection]):
        return max(map(len, obj), default=0)

    def table(
        self,
        name: str,
        head: Collection[Collection],
        body: Collection[Collection],
        footer: Collection[Collection],
    ):
        # Add one extra row for the heading with the name
        rows = len(head) + len(body) + len(footer) + 1
        cols = max(map(self._max_cols, (head, body, footer)), default=0)
        if not cols:
            raise RuntimeError("No columns found in head, body or footer")

        table = self.doc.add_table(rows, cols, style="Stat Table")
        set_table_border(table)
        set_table_caption(table, name)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        cell = table.cell(0, 0)
        for col in range(1, cols):
            cell.merge(table.cell(0, col))

        self.th(table, 0, 0, name)

        row_index = 1
        for part, func in (head, self.th), (body, self.td), (footer, self.tf):
            for row in part:
                for col_index, data in enumerate(row):
                    if data is not None:
                        func(table, row_index, col_index, str(data))
                row_index += 1

        return table

    def th(self, table, row, col, text):
        return set_cell(
            table=table,
            row=row,
            col=col,
            text=text,
            style="Table Header",
            align=WD_PARAGRAPH_ALIGNMENT.CENTER,
            v_align=WD_CELL_VERTICAL_ALIGNMENT.CENTER,
            bg_color="#a5c9eb",
        )

    def td(self, table, row, col, text):
        return set_cell(
            table=table,
            row=row,
            col=col,
            text=str(text),
            style="Table Data",
            align=WD_PARAGRAPH_ALIGNMENT.RIGHT if col != 0 else None,
        )

    def tf(self, table, row, col, text):
        return set_cell(
            table=table,
            row=row,
            col=col,
            text=str(text),
            style="Table Footer",
            align=WD_PARAGRAPH_ALIGNMENT.RIGHT if col != 0 else None,
        )

    def _format_percent(self, value, total):
        if total == 0:
            return "-"
        value = Decimal(value) / Decimal(total) * 100
        return str(value.quantize(Decimal("0.01"))) + "%"

    def get_content(self):
        self.doc.add_paragraph()

        p = self.doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        p.add_run(timezone.now().date().strftime("%-d %B %Y"))

        p = self.doc.add_paragraph()
        r = p.add_run("Meeting Participants statistics: Registration and A5 funding")
        r.font.bold = True

        self.table_pax_by_category()
        self.doc.add_paragraph()

        self.table_parties_by_region()
        self.doc.add_paragraph()

        for region in self.regions:
            self.table_parties_by_subregion(region)
            self.doc.add_paragraph()

    def table_pax_by_category(self):
        counts = dict.fromkeys(
            (
                org_type.statistics_display_name
                for org_type in OrganizationType.objects.filter(
                    hide_in_statistics=False
                ).order_by("sort_order", "statistics_title", "title")
            ),
            0,
        )
        for registration in self.accredited_registrations:
            try:
                org = registration.usable_organization
                name = org.organization_type.statistics_display_name
            except AttributeError:
                name = "Unknown"
            if name not in counts:
                counts[name] = 0
            counts[name] += 1

        self.table(
            "Table 1: Registered participants",
            [
                ("Category", "Registered"),
            ],
            [(category, count) for category, count in counts.items()],
            [
                ("Total", str(len(self.accredited_registrations))),
            ],
        )

    def table_parties_by_region(self):
        total = len(self.accredited_gov_parties)
        counts = dict.fromkeys(self.regions, 0)
        for party in self.accredited_gov_parties:
            counts[party.region] += 1

        self.table(
            "Table 2: Registered Parties",
            [
                ("Category", "Registered", "% of total", "% in category"),
            ],
            [
                (
                    f"{region} Parties",
                    count,
                    self._format_percent(count, total),
                    self._format_percent(count, region.countries.count()),
                )
                for region, count in counts.items()
            ],
            [
                ("Total", str(total), "", ""),
            ],
        )

    def table_parties_by_subregion(self, region):
        all_parties = Counter(
            (
                country.subregion
                for country in region.countries.all().order_by("subregion__name")
            )
        )
        accredited_parties = Counter(
            (
                country.subregion
                for country in self.accredited_gov_parties
                if country.region == region
            )
        )
        accredited_registrations = Counter(
            (
                registration.usable_government.subregion
                for registration in self.accredited_gov_registrations
                if registration.usable_government.region == region
            )
        )
        table = self.table(
            f"Table 3: {region} Parties",
            [
                (
                    "Region",
                    "Parties per region",
                    "Parties registered",
                    "Parties to register",
                    "Participants registered",
                    "Funding Requested",
                    None,
                    "Reserved Slots",
                    "Remarks",
                ),
                (None, "(a)", "(b)", "(a - b)", None, "Received", "Approved"),
            ],
            [
                (
                    subregion.name,
                    count,
                    accredited_parties[subregion],
                    count - accredited_parties[subregion],
                    accredited_registrations[subregion],
                )
                for subregion, count in all_parties.items()
            ],
            [
                (
                    "Total",
                    sum(all_parties.values()),
                    sum(accredited_parties.values()),
                    sum(all_parties.values()) - sum(accredited_parties.values()),
                    sum(accredited_registrations.values()),
                )
            ],
        )

        table.cell(1, 0).merge(table.cell(2, 0))
        table.cell(1, 4).merge(table.cell(2, 4))
        table.cell(1, 5).merge(table.cell(1, 6))
        table.cell(1, 7).merge(table.cell(2, 7))
        table.cell(1, 8).merge(table.cell(2, 8))

    def save_docx(self):
        doc_file = io.BytesIO()
        doc_file.name = f"{self.event.code}-statistics.docx"
        self.doc.save(doc_file)
        doc_file.seek(0)
        return doc_file
