"""Build a portable, native-schema Tableau workbook from the BI export.

The XML template in ``bi/tableau-native-template.twb`` was saved by Tableau
Desktop 2026.2 with the CSV source connected. Keep workbook generation limited
to Tableau's native workbook structure; opening the packaged TWBX in Tableau is
still the final render check.
"""

import csv
import json
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "bi"
TEMPLATE = BI / "tableau-native-template.twb"
DS = "federated.1rmj6q21e8bkj6194b3dt0euhk1e"
CAPTION = "Atlas synthetic portfolio"


def child(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, tag, {k.replace("_", "-"): str(v) for k, v in attrs.items()})
    node.text = text
    return node


def field(name, datatype, role, kind, caption=None, calculation=None):
    attrs = {"name": f"[{name}]", "datatype": datatype, "role": role, "type": kind}
    if caption:
        attrs["caption"] = caption
    node = ET.Element("column", attrs)
    if calculation:
        child(node, "calculation", formula=calculation, **{"class": "tableau"})
    return node


def stable_uuid(name):
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"atlas-commercial-intelligence:{name}")).upper() + "}"


FIELDS = {
    "month": ("date", "dimension", "ordinal", "Month"),
    "product": ("string", "dimension", "nominal", "Product"),
    "category": ("string", "dimension", "nominal", "Category"),
    "country": ("string", "dimension", "nominal", "Country"),
    "territory": ("string", "dimension", "nominal", "Territory"),
    "channel": ("string", "dimension", "nominal", "Channel"),
    "revenue": ("real", "measure", "quantitative", "Revenue"),
    "target": ("real", "measure", "quantitative", "Target"),
    "gap": ("real", "measure", "quantitative", "Gap"),
    "units": ("integer", "measure", "quantitative", "Units"),
    "promotion": ("boolean", "dimension", "nominal", "Promotion"),
}


SHEETS = [
    ("Monthly Revenue", "month", "revenue", "Line"),
    ("Revenue by Market", "country", "revenue", "Bar"),
    ("Product Plan Variance", "product", "gap", "Bar"),
    ("Attainment by Market", "country", "attainment", "Bar"),
    ("Revenue by Channel", "channel", "revenue", "Bar"),
    ("Portfolio Revenue", None, "revenue", "Text"),
]


def make_worksheet(name, dimension, measure):
    worksheet = ET.Element("worksheet", {"name": name})
    options = child(worksheet, "layout-options")
    title = child(options, "title")
    formatted = child(title, "formatted-text")
    child(formatted, "run", name)

    table = child(worksheet, "table")
    view = child(table, "view")
    datasources = child(view, "datasources")
    child(datasources, "datasource", caption=CAPTION, name=DS)
    dependencies = child(view, "datasource-dependencies", datasource=DS)

    needed = {measure} | ({dimension} if dimension else set())
    if measure == "attainment":
        needed.update({"revenue", "target"})
    for name in sorted(needed):
        if name == "attainment":
            dependencies.append(field("attainment_calc", "real", "measure", "quantitative", "Attainment", "SUM([revenue]) / SUM([target])"))
        else:
            datatype, role, kind, caption = FIELDS[name]
            dependencies.append(field(name, datatype, role, kind, caption))

    measure_column = "attainment_calc" if measure == "attainment" else measure
    measure_name = f"[sum:{measure_column}:qk]" if measure != "attainment" else "[usr:attainment_calc:qk]"
    measure_derivation = "Sum" if measure != "attainment" else "User"
    child(dependencies, "column-instance", column=f"[{measure_column}]", derivation=measure_derivation, name=measure_name, pivot="key", type="quantitative")

    dimension_name = None
    if dimension:
        if dimension == "month":
            dimension_name = "[tmn:month:ok]"
            derivation = "Month-Trunc"
            kind = "ordinal"
        else:
            dimension_name = f"[none:{dimension}:nk]"
            derivation = "None"
            kind = "nominal"
        child(dependencies, "column-instance", column=f"[{dimension}]", derivation=derivation, name=dimension_name, pivot="key", type=kind)

    child(view, "aggregation", value="true")
    child(table, "style")
    panes = child(table, "panes")
    pane = child(panes, "pane", **{"selection-relaxation-option": "selection-relaxation-allow"})
    pane_view = child(pane, "view")
    child(pane_view, "breakdown", value="auto")
    child(pane, "mark", **{"class": "Line" if dimension == "month" else "Bar" if dimension else "Text"})
    encodings = child(pane, "encodings")
    measure_ref = f"[{DS}].{measure_name}"
    if dimension:
        if dimension == "month":
            child(encodings, "color", column=measure_ref)
        else:
            child(encodings, "color", column=f"[{DS}].{dimension_name}")
    else:
        child(encodings, "text", column=measure_ref)
    if dimension == "month":
        rows = measure_ref
        cols = f"[{DS}].{dimension_name}"
    elif dimension:
        rows = f"[{DS}].{dimension_name}"
        cols = measure_ref
    else:
        rows, cols = "", ""
    child(table, "rows", rows)
    child(table, "cols", cols)
    child(worksheet, "simple-id", uuid=stable_uuid(f"worksheet:{name}"))
    return worksheet


def make_dashboard(name):
    dashboard = ET.Element("dashboard", {"name": name})
    options = child(dashboard, "layout-options")
    title = child(options, "title")
    formatted = child(title, "formatted-text")
    child(formatted, "run", "COMMERCIAL PERFORMANCE REVIEW", fontsize="18", bold="true")
    child(dashboard, "size", minwidth="1200", minheight="800")
    zones = child(dashboard, "zones")
    root = child(zones, "zone", id="1", type_v2="layout-basic", x="0", y="0", w="100000", h="100000")
    vertical = child(root, "zone", id="2", type_v2="layout-flow", param="vert", x="0", y="0", w="100000", h="100000")
    for row_index in range(2):
        row = child(vertical, "zone", id=str(10 + row_index), type_v2="layout-flow", param="horz", x="0", y=str(row_index * 50000), w="100000", h="50000")
        for col_index in range(3):
            sheet_index = row_index * 3 + col_index
            sheet_name = SHEETS[sheet_index][0]
            child(row, "zone", id=str(20 + sheet_index), name=sheet_name, x=str(col_index * 33333), y="0", w="33333", h="46500")
    return dashboard


def workbook_bytes(directory):
    root = ET.parse(TEMPLATE).getroot()
    for attr in list(root.attrib):
        if "machine-id" in attr or "author-id" in attr or "license-type" in attr:
            del root.attrib[attr]

    source = root.find("./datasources/datasource")
    source.attrib["caption"] = CAPTION
    connection = source.find("./connection/named-connections/named-connection/connection")
    connection.attrib["directory"] = directory
    connection.attrib["filename"] = "portfolio.csv"
    named = source.find("./connection/named-connections/named-connection")
    named.attrib["caption"] = CAPTION
    for node in source.findall(".//relation"):
        node.attrib["name"] = "portfolio.csv"
        node.attrib["table"] = "[portfolio#csv]"
    for node in source.iter():
        for key, value in list(node.attrib.items()):
            node.attrib[key] = value.replace("atlas-portfolio.csv", "portfolio.csv")
        if node.text:
            node.text = node.text.replace("atlas-portfolio.csv", "portfolio.csv")
    for node in source.findall("./column"):
        if "caption" in node.attrib:
            node.attrib["caption"] = FIELDS.get(node.attrib["name"].strip("[]"), (None, None, None, node.attrib["caption"]))[3]

    worksheets = root.find("./worksheets")
    for old in list(worksheets):
        worksheets.remove(old)
    for spec in SHEETS:
        worksheets.append(make_worksheet(*spec[:3]))

    dashboards = root.find("./dashboards")
    if dashboards is None:
        dashboards = ET.SubElement(root, "dashboards")
    for old in list(dashboards):
        dashboards.remove(old)
    dashboards.append(make_dashboard("Commercial performance review"))

    windows = root.find("./windows")
    for window in list(windows):
        windows.remove(window)
    window = child(windows, "window", **{"class": "dashboard", "maximized": "true", "name": "Commercial performance review"})
    cards = child(window, "cards")
    left = child(cards, "edge", name="left")
    strip = child(left, "strip", size="160")
    child(strip, "card", type="filters")
    child(window, "simple-id", uuid=stable_uuid("dashboard-window"))

    thumbnails = root.find("./thumbnails")
    if thumbnails is not None:
        for thumbnail in list(thumbnails):
            thumbnails.remove(thumbnail)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main():
    with (BI / "portfolio.csv").open(newline="", encoding="utf-8") as file:
        rows = sum(1 for _ in csv.DictReader(file))
    expected = json.loads((BI / "manifest.json").read_text(encoding="utf-8"))["export_rows"]
    if rows != expected:
        raise ValueError(f"CSV row count {rows} does not match manifest {expected}")

    standalone = workbook_bytes(".")
    packaged = workbook_bytes("Data")
    (BI / "atlas-commercial-review.twb").write_bytes(standalone)
    with zipfile.ZipFile(BI / "atlas-commercial-review.twbx", "w", zipfile.ZIP_DEFLATED) as package:
        def add_file(name, content):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, content)

        add_file("atlas-commercial-review.twb", packaged)
        add_file("Data/portfolio.csv", (BI / "portfolio.csv").read_bytes())
        add_file("Data/manifest.json", (BI / "manifest.json").read_bytes())

    parsed = ET.fromstring(packaged)
    assert len(parsed.findall("./worksheets/worksheet")) == len(SHEETS)
    assert parsed.find("./dashboards/dashboard") is not None
    print(f"Built native-schema Tableau workbook with {len(SHEETS)} worksheets, 1 dashboard, and {rows:,} synthetic rows.")


if __name__ == "__main__":
    main()
