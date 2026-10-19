"""Build a portable Tableau workbook from the shared BI export.

TWB XML is generated locally; opening in Tableau is a separate release gate.
"""

import copy
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "bi"
SOURCE = "atlas_portfolio"


def node(parent, tag, text=None, **attrs):
    item = ET.SubElement(
        parent, tag, {k.replace("_", "-"): str(v) for k, v in attrs.items()}
    )
    item.text = text
    return item


def main():
    fields = [
        ("month", "date", "dimension", "ordinal"),
        ("product", "string", "dimension", "nominal"),
        ("category", "string", "dimension", "nominal"),
        ("country", "string", "dimension", "nominal"),
        ("territory", "string", "dimension", "nominal"),
        ("channel", "string", "dimension", "nominal"),
        ("revenue", "real", "measure", "quantitative"),
        ("units", "integer", "measure", "quantitative"),
        ("target", "real", "measure", "quantitative"),
        ("promotion", "boolean", "dimension", "nominal"),
        ("gap", "real", "measure", "quantitative"),
        ("attainment", "real", "measure", "quantitative"),
        ("prior_year_revenue", "real", "measure", "quantitative"),
    ]
    root = ET.Element("workbook", {"version": "9.3", "source-platform": "mac"})
    source = node(
        node(root, "datasources"),
        "datasource",
        name=SOURCE,
        caption="Atlas synthetic portfolio",
        inline="true",
        version="9.3",
    )
    connection = node(
        source,
        "connection",
        **{
            "class": "textscan",
            "directory": "Data",
            "filename": "portfolio.csv",
            "separator": ",",
            "header": "yes",
            "charset": "UTF-8",
        },
    )
    node(
        connection,
        "relation",
        name="portfolio.csv",
        table="[portfolio.csv]",
        type="table",
    )
    columns = {}
    for name, dtype, role, kind in fields:
        columns[name] = node(
            source, "column", name=f"[{name}]", datatype=dtype, role=role, type=kind
        )
    calculations = {
        "Attainment": "SUM([revenue]) / SUM([target])",
        "Growth": "IF COUNT([prior_year_revenue]) = COUNT([revenue]) THEN SUM([revenue]) / SUM([prior_year_revenue]) - 1 END",
    }
    for name, formula in calculations.items():
        columns[name] = node(
            source,
            "column",
            name=f"[{name}]",
            datatype="real",
            role="measure",
            type="quantitative",
        )
        node(columns[name], "calculation", formula=formula, **{"class": "tableau"})
    sheets = node(root, "worksheets")
    specs = [
        ("Revenue · USD", None, "revenue"),
        ("Target attainment", None, "Attainment"),
        ("Year-over-year growth", None, "Growth"),
        ("Monthly revenue", "month", "revenue"),
        ("Market gap · USD", "country", "gap"),
        ("Product gap · USD", "product", "gap"),
    ]
    for title, dimension, measure in specs:
        sheet = node(sheets, "worksheet", name=title)
        table = node(sheet, "table")
        view = node(table, "view")
        node(
            node(view, "datasources"),
            "datasource",
            name=SOURCE,
            caption="Atlas synthetic portfolio",
        )
        dependencies = node(view, "datasource-dependencies", datasource=SOURCE)
        needed = {measure, "month", "country"} | ({dimension} if dimension else set())
        if measure in calculations:
            needed |= {"revenue", "target", "prior_year_revenue"}
        for field in sorted(needed):
            dependencies.append(copy.deepcopy(columns[field]))
        derived = "usr" if measure in calculations else "sum"
        measure_ref = f"[{derived}:{measure}:qk]"
        node(
            dependencies,
            "column-instance",
            column=f"[{measure}]",
            derivation="User" if derived == "usr" else "Sum",
            name=measure_ref,
            pivot="key",
            type="quantitative",
        )
        if dimension:
            dim_ref = f"[none:{dimension}:nk]"
            node(
                dependencies,
                "column-instance",
                column=f"[{dimension}]",
                derivation="None",
                name=dim_ref,
                pivot="key",
                type="nominal",
            )
        # Every sheet starts at the same Q3 2026 reporting scope.
        filter_node = node(
            view, "filter", column=f"[{SOURCE}].[month]", **{"class": "quantitative"}
        )
        node(filter_node, "min", "#2026-07-01#")
        node(filter_node, "max", "#2026-09-01#")
        node(view, "aggregation", value="true")
        node(table, "style")
        pane = node(node(table, "panes"), "pane")
        node(node(pane, "view"), "breakdown", value="auto")
        node(
            pane,
            "mark",
            **{
                "class": "Line"
                if dimension == "month"
                else "Bar"
                if dimension
                else "Text"
            },
        )
        if not dimension:
            node(node(pane, "encodings"), "text", column=f"[{SOURCE}].{measure_ref}")
        node(
            table,
            "rows",
            f"[{SOURCE}].{measure_ref}"
            if dimension == "month"
            else f"[{SOURCE}].{dim_ref}"
            if dimension
            else None,
        )
        node(
            table,
            "cols",
            f"[{SOURCE}].{dim_ref}"
            if dimension == "month"
            else f"[{SOURCE}].{measure_ref}"
            if dimension
            else None,
        )
    dashboard = node(
        node(root, "dashboards"),
        "dashboard",
        name="Atlas · Commercial review · Synthetic data",
    )
    node(dashboard, "style")
    node(
        dashboard,
        "size",
        sizing_mode="fixed",
        minwidth="1200",
        maxwidth="1200",
        minheight="800",
        maxheight="800",
    )
    zones = node(dashboard, "zones")
    for i, (title, _, _) in enumerate(specs):
        x, y, w, h = (
            (i * 33333, 0, 33333, 22000)
            if i < 3
            else ((i - 3) * 33333, 22000, 33333, 78000)
        )
        node(zones, "zone", id=i + 1, name=title, x=x, y=y, w=w, h=h)
    ET.indent(root)
    workbook = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    (BI / "atlas-commercial-review.twb").write_bytes(workbook)
    with zipfile.ZipFile(
        BI / "atlas-commercial-review.twbx", "w", zipfile.ZIP_DEFLATED
    ) as package:
        package.writestr("atlas-commercial-review.twb", workbook)
        package.write(BI / "portfolio.csv", "Data/portfolio.csv")
        package.write(BI / "manifest.json", "Data/manifest.json")
    assert len(ET.fromstring(workbook).findall("./worksheets/worksheet")) == 6
    with (BI / "portfolio.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == json.loads((BI / "manifest.json").read_text())["export_rows"]
    print(
        "Packaged six worksheets, a dashboard, and 12,288 synthetic rows. Native Tableau rendering remains to verify."
    )


if __name__ == "__main__":
    main()
