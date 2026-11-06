#!/usr/bin/env python3
"""Generates App.fx.yaml and CampaignRequestScreen.fx.yaml for the Campaign Request Form.

Layout comes from the Figma frame `scrCampaignRequest_Simple` (1366 x 2375).
Colours and control style come from the AV Central Deposit canvas-source.
Usage: gen_campaign_app.py <canvas-source dir>
"""
import sys
import os

OUT = sys.argv[1]

# ---------------------------------------------------------------- palette (from AV Central Deposit msapp)
NAVY = "RGBA(0, 18, 107, 1)"
BLUE = "RGBA(56, 96, 178, 1)"
LIGHTBLUE = "RGBA(186, 202, 226, 1)"
TINT = "RGBA(230, 236, 245, 1)"
BG = "RGBA(247, 248, 250, 1)"
WHITE = "RGBA(255, 255, 255, 1)"
CLEAR = "RGBA(0, 0, 0, 0)"
BORDER = "RGBA(220, 224, 230, 1)"
INPUTBORDER = "RGBA(186, 196, 214, 1)"
TEXT = "RGBA(60, 66, 80, 1)"
MUTED = "RGBA(96, 104, 120, 1)"
DISABLED = "RGBA(140, 148, 160, 1)"
GREYBG = "RGBA(240, 242, 246, 1)"
GREEN = "RGBA(22, 128, 80, 1)"
GREENBG = "RGBA(240, 253, 244, 1)"
RED = "RGBA(193, 40, 40, 1)"
REDBG = "RGBA(254, 242, 242, 1)"
REDBORDER = "RGBA(254, 202, 202, 1)"
AMBER = "RGBA(245, 158, 11, 1)"
AMBERTXT = "RGBA(180, 95, 6, 1)"
AMBERBG = "RGBA(254, 243, 199, 1)"


def s(text):
    """Power Fx string literal."""
    return '"' + text.replace('"', '""') + '"'


# ---------------------------------------------------------------- YAML emitters
def emit_prop(key, formula, indent):
    pad = " " * indent
    f = str(formula)
    if "\n" in f or ": " in f or " #" in f or f.rstrip().endswith(":"):
        lines = f.split("\n")
        out = [f"{pad}{key}: |-"]
        out.append(f"{pad}    ={lines[0]}")
        for ln in lines[1:]:
            assert ln.strip() != "", "blank line inside formula (breaks fx.yaml parser)"
            out.append(f"{pad}    {ln}")
        return out
    return [f"{pad}{key}: ={f}"]


class Scope:
    def __init__(self):
        self.z = 0

    def next(self):
        self.z += 1
        return self.z


def ctl(scope, name, typ, indent, props, children=None):
    props = dict(props)
    props["ZIndex"] = scope.next()
    out = [f"{' ' * indent}{name} As {typ}:"]
    for k in sorted(props):
        out += emit_prop(k, props[k], indent + 4)
    if children:
        out.append("")
        out += children
    out.append("")
    return out


# ---------------------------------------------------------------- shared formulas
VARS_RESET = [
    '"Draft"|varStatus',
    '"CR" & Text(CountRows(colCampaignRequests) + 1, "0000")|varRequestId',
    '""|varTitle',
    'User().FullName|varLead',
    '""|varDG',
    '""|varBudget',
    '""|varObjective',
    'Blank()|varStartDate',
    'Blank()|varEndDate',
    '""|varOutcome',
    '""|varKpiViews',
    '""|varKpiVTR',
    '""|varKpiSubs',
    '""|varKpiCPS',
    '""|varKpiOther',
    '""|varAges',
    '"All"|varGender',
    '""|varLanguages',
    '""|varCountries',
    '""|varInterests',
    '0|varAttachCount',
    'false|varContractorOn',
    '""|varContractor',
    '""|varContractRef',
    'Blank()|varReportDue',
    'false|varAck1',
    'false|varAck2',
    '""|varNotes',
    '"General"|varActiveSection',
]


def reset_block():
    lines = []
    for item in VARS_RESET:
        val, name = item.rsplit("|", 1)
        lines.append(f"Set({name}, {val});")
    return "\n".join(lines).rstrip(";")


def save_block(status):
    return (
        "RemoveIf(colCampaignRequests, RequestId = varRequestId);\n"
        "Collect(\n"
        "    colCampaignRequests,\n"
        "    {\n"
        "        RequestId: varRequestId,\n"
        f'        Status: "{status}",\n'
        "        Title: varTitle,\n"
        "        CampaignLead: varLead,\n"
        "        DGUnit: varDG,\n"
        "        EstimatedBudgetEUR: varBudget,\n"
        "        PrimaryObjective: varObjective,\n"
        "        StartDate: varStartDate,\n"
        "        EndDate: varEndDate,\n"
        "        ObjectiveOutcome: varOutcome,\n"
        "        KpiEngagedViews: varKpiViews,\n"
        "        KpiViewThroughRate: varKpiVTR,\n"
        "        KpiNewSubscribers: varKpiSubs,\n"
        "        KpiCostPerSubscriber: varKpiCPS,\n"
        "        OtherKpis: varKpiOther,\n"
        "        AgeRanges: varAges,\n"
        "        Gender: varGender,\n"
        "        Languages: varLanguages,\n"
        "        CountriesRegions: varCountries,\n"
        "        Interests: varInterests,\n"
        "        AttachmentCount: varAttachCount,\n"
        "        ContractorEngaged: varContractorOn,\n"
        "        Contractor: varContractor,\n"
        "        ContractReference: varContractRef,\n"
        "        FinalReportDue: varReportDue,\n"
        "        AckUnlisted: varAck1,\n"
        "        AckCommentsDisabled: varAck2,\n"
        "        Observations: varNotes,\n"
        "        SavedOn: Now(),\n"
        "        SavedBy: User().Email\n"
        "    }\n"
        ")"
    )


def num_ok(v):
    return f"Not(IsBlank({v})) And Not(IsError(Value({v})))"


def started(vs):
    return " Or ".join(f"Not(IsBlank({v}))" for v in vs)


STAT_GENERAL = (
    "If(\n"
    "    Not(IsBlank(varTitle)) And Not(IsBlank(varLead)) And Not(IsBlank(varDG)),\n"
    '    "Complete",\n'
    f'    If({started(["varTitle", "varDG", "varBudget"])}, "Needs review", "Not started")\n'
    ")"
)
STAT_OBJECTIVES = (
    "If(\n"
    "    Not(IsBlank(varObjective)) And Not(IsBlank(varStartDate)) And Not(IsBlank(varEndDate)) And varEndDate >= varStartDate\n"
    f"        And Not(IsBlank(varOutcome)) And {num_ok('varKpiViews')} And {num_ok('varKpiSubs')},\n"
    '    "Complete",\n'
    f'    If({started(["varObjective", "varStartDate", "varEndDate", "varOutcome", "varKpiViews", "varKpiVTR", "varKpiSubs", "varKpiCPS", "varKpiOther"])}, "Needs review", "Not started")\n'
    ")"
)
STAT_AUDIENCE = (
    "If(\n"
    "    Not(IsBlank(varAges)) And Not(IsBlank(varLanguages)) And Not(IsBlank(varCountries)),\n"
    '    "Complete",\n'
    f'    If({started(["varAges", "varLanguages", "varCountries", "varInterests"])}, "Needs review", "Not started")\n'
    ")"
)
STAT_ATTACH = 'If(varAttachCount > 0, "Complete", "Not started")'
STAT_DELIVERY = (
    "If(\n"
    "    varAck1 And varAck2 And (Not(varContractorOn) Or Not(IsBlank(varContractor))),\n"
    '    "Complete",\n'
    "    If(\n"
    "        varContractorOn Or varAck1 Or varAck2 Or Not(IsBlank(varContractor)) Or Not(IsBlank(varContractRef)) Or Not(IsBlank(varReportDue)) Or Not(IsBlank(varNotes)),\n"
    '        "Needs review",\n'
    '        "Not started"\n'
    "    )\n"
    ")"
)


def by_status(stat, complete, review, notstarted):
    return f'Switch({stat}.Text, "Complete", {complete}, "Needs review", {review}, {notstarted})'


# ---------------------------------------------------------------- App.fx.yaml
def write_app():
    init = (
        "ClearCollect(colCampaignRequests, {RequestId: \"\", Status: \"\", Title: \"\"});\n"
        "Clear(colCampaignRequests);\n" + reset_block()
    )
    lines = ["App As appinfo:", "    BackEnabled: =false", "    OnStart: |-"]
    for idx, ln in enumerate(init.split("\n")):
        assert ln.strip() != "", "blank line inside OnStart (breaks fx.yaml parser)"
        lines.append(f"        {'=' if idx == 0 else ''}{ln}")
    lines += [
        "    StartScreen: =CampaignRequestScreen",
        "    Theme: =PowerAppsTheme",
        "",
        "    Host As hostControl.DefaultHostControlVariant:",
        "        OnCancel: =false",
        "        OnEdit: =false",
        "        OnNew: =false",
        "        OnSave: =false",
        "        OnView: =false",
        "",
    ]
    with open(os.path.join(OUT, "Src", "App.fx.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------- screen
def build_screen():
    sc = Scope()
    body = []

    def label(name, text, x, y, w, h, size=12, color=TEXT, weight="Semibold", align=None, valign=None,
              fill=None, visible=None, indent=4, scope=None, extra=None):
        p = {"Color": color, "FontWeight": f"FontWeight.{weight}", "Height": h, "Size": size,
             "Text": text, "Width": w, "X": x, "Y": y}
        if align:
            p["Align"] = f"Align.{align}"
        if valign:
            p["VerticalAlign"] = f"VerticalAlign.{valign}"
        if fill:
            p["Fill"] = fill
        if visible:
            p["Visible"] = visible
        if extra:
            p.update(extra)
        return ctl(scope or sc, name, "label", indent, p)

    def rect(name, x, y, w, h, fill, border=None, bt=None, visible=None, indent=4, scope=None):
        p = {"Fill": fill, "Height": h, "Width": w, "X": x, "Y": y}
        if border:
            p["BorderColor"] = border
            p["BorderThickness"] = bt if bt is not None else 1
        if visible:
            p["Visible"] = visible
        return ctl(scope or sc, name, "rectangle", indent, p)

    def circle(name, x, y, d, fill, border=None, indent=4, scope=None, extra=None):
        p = {"Fill": fill, "Height": d, "Width": d, "X": x, "Y": y}
        if border:
            p["BorderColor"] = border
            p["BorderThickness"] = 1
        if extra:
            p.update(extra)
        return ctl(scope or sc, name, "circle", indent, p)

    def button(name, text, x, y, w, h, fill, color, onselect=None, border=None, hover=None, radius=4,
               size=12, align=None, extra=None, indent=4, scope=None):
        p = {"Color": color, "Fill": fill, "Height": h, "Size": size, "Text": text, "Width": w, "X": x, "Y": y,
             "FontWeight": "FontWeight.Semibold",
             "BorderThickness": 1 if border else 0,
             "RadiusTopLeft": radius, "RadiusTopRight": radius, "RadiusBottomLeft": radius, "RadiusBottomRight": radius}
        if border:
            p["BorderColor"] = border
        if hover:
            p["HoverFill"] = hover
        if onselect:
            p["OnSelect"] = onselect
        if align:
            p["Align"] = f"Align.{align}"
        if extra:
            p.update(extra)
        return ctl(scope or sc, name, "button", indent, p)

    # ============================== header ==============================
    body += rect("HdrBar", 0, 0, 1366, 56, NAVY)
    body += rect("HdrLogoBox", 20, 12, 32, 32, BLUE)
    body += label("HdrLogoGlyph", s("▶"), 20, 12, 32, 32, size=11, color=WHITE, align="Center", valign="Middle")
    body += label("HdrTitle", s("Campaign Requests"), 64, 17, 170, 22, size=14, color=WHITE)
    body += label("HdrSep", s("/"), 231, 17, 10, 22, size=14, color=LIGHTBLUE, weight="Normal")
    body += label("HdrCrumb", s("New request"), 247, 18, 200, 20, size=12, color=LIGHTBLUE, weight="Normal")
    body += label("HdrRequestId", "varRequestId", 800, 18, 100, 20, size=12, color=WHITE, align="Right")
    body += button("HdrStatusBadge", "varStatus", 908, 17, 72, 22,
                   'If(varStatus = "Submitted", RGBA(223, 245, 233, 1), RGBA(230, 236, 245, 1))',
                   'If(varStatus = "Submitted", RGBA(22, 128, 80, 1), RGBA(0, 18, 107, 1))',
                   border=LIGHTBLUE, radius=11, size=10, extra={"DisplayMode": "DisplayMode.View"})
    body += circle("HdrAvatar", 992, 12, 32, TINT)
    body += label("HdrAvatarText",
                  'Upper(Left(User().FullName, 1)) & Upper(Mid(User().FullName, Find(" ", User().FullName & " ") + 1, 1))',
                  992, 12, 32, 32, size=10, color=NAVY, align="Center", valign="Middle")
    body += label("HdrUserName", "User().FullName", 1036, 17, 310, 22, size=12, color=WHITE, weight="Normal")

    # ============================== side menu ==============================
    body += rect("SideBg", 0, 56, 240, 712, WHITE)
    body += rect("SideDivider", 239, 56, 1, 712, BORDER)
    body += label("SideTitle", s("Sections"), 24, 76, 150, 16, size=10, color=MUTED)

    tabs = [("General", "General", "StatGeneral"),
            ("Objectives & KPIs", "Objectives", "StatObjectives"),
            ("Audience", "Audience", "StatAudience"),
            ("Attachments", "Attachments", "StatAttachments"),
            ("Delivery", "Delivery", "StatDelivery")]
    for i, (title, key, stat) in enumerate(tabs):
        y = 102 + i * 42
        sel = f'varActiveSection = "{key}"'
        body += button(f"Tab{key}", s(title), 12, y, 215, 40,
                       f"If({sel}, {TINT}, {CLEAR})", f"If({sel}, {NAVY}, {TEXT})",
                       onselect=f'Set(varActiveSection, "{key}")', hover=GREYBG, radius=0, size=12, align="Left",
                       extra={"PaddingLeft": 14, "FocusedBorderThickness": 0})
        body += rect(f"Tab{key}Indicator", 12, y + 10, 3, 20, BLUE, visible=sel)
        body += circle(f"Tab{key}Dot", 201, y + 12, 16,
                       by_status(stat, GREEN, AMBER, WHITE),
                       border=by_status(stat, GREEN, AMBER, DISABLED))
        body += label(f"Tab{key}Glyph",
                      by_status(stat, s("✓"), s("!"), s("")),
                      201, y + 12, 16, 16, size=9, color=WHITE, align="Center", valign="Middle")

    body += label("ProgressText", 'StatCount.Text & " of 5 sections complete"', 24, 332, 190, 16, size=10, color=MUTED)
    body += rect("ProgressTrack", 24, 356, 191, 2, BORDER)
    body += rect("ProgressFill", 24, 356, "191 * Value(StatCount.Text) / 5", 2, BLUE)
    legend = [("Complete", GREEN, GREEN, s("✓")),
              ("Needs review", AMBER, AMBER, s("!")),
              ("Not started", WHITE, DISABLED, s(""))]
    for i, (txt, fill, border, glyph) in enumerate(legend):
        y = 374 + i * 22
        body += circle(f"Legend{i}Dot", 24, y, 16, fill, border=border)
        body += label(f"Legend{i}Glyph", glyph, 24, y, 16, 16, size=9, color=WHITE, align="Center", valign="Middle")
        body += label(f"Legend{i}Text", s(txt), 46, y, 150, 16, size=10, color=MUTED, weight="Normal")

    # hidden calculation cells (screen level, referenced by side menu and gallery)
    calc = [("StatGeneral", STAT_GENERAL), ("StatObjectives", STAT_OBJECTIVES), ("StatAudience", STAT_AUDIENCE),
            ("StatAttachments", STAT_ATTACH), ("StatDelivery", STAT_DELIVERY)]
    for name, f in calc:
        body += label(name, f, 0, 0, 10, 10, visible="false")
    count = ("Text(CountRows(Filter([StatGeneral.Text, StatObjectives.Text, StatAudience.Text, "
             "StatAttachments.Text, StatDelivery.Text], Value = \"Complete\")))")
    body += label("StatCount", count, 0, 0, 10, 10, visible="false")
    body += label("StatMissing",
                  'If(StatGeneral.Text <> "Complete", "General", If(StatObjectives.Text <> "Complete", "Objectives & KPIs", '
                  'If(StatAudience.Text <> "Complete", "Audience", "Delivery")))',
                  0, 0, 10, 10, visible="false")
    body += label("StatAll",
                  'StatGeneral.Text = "Complete" And StatObjectives.Text = "Complete" And StatAudience.Text = "Complete" And StatDelivery.Text = "Complete"',
                  0, 0, 10, 10, visible="false")

    # ============================== scrolling content (gallery) ==============================
    gz = Scope()
    g = []
    IND = 8

    def gl(*a, **k):
        k.update(indent=IND, scope=gz)
        return label(*a, **k)

    def gr(*a, **k):
        k.update(indent=IND, scope=gz)
        return rect(*a, **k)

    def gc(*a, **k):
        k.update(indent=IND, scope=gz)
        return circle(*a, **k)

    def gb(*a, **k):
        k.update(indent=IND, scope=gz)
        return button(*a, **k)

    def field_label(name, text, x, y, w, required=False):
        t = text + (" *" if required else "")
        return gl(name, s(t), x, y, w, 20, size=12, color=TEXT)

    def helper(name, text, x, y, w):
        return gl(name, s(text), x, y, w, 16, size=10, color=MUTED, weight="Normal")

    def text_input(name, x, y, w, var, hint, h=32, multiline=False, numeric=False, extra=None):
        p = {"BorderColor": INPUTBORDER, "BorderThickness": 1, "Color": TEXT, "Default": var, "Fill": WHITE,
             "Height": h, "HintText": s(hint), "OnChange": f"Set({var}, Self.Value)", "Size": 12,
             "Width": w, "X": x, "Y": y}
        if multiline:
            p["Mode"] = "TextMode.MultiLine"
        if numeric:
            p["BorderColor"] = f"If(Not(IsBlank(Self.Value)) And IsError(Value(Self.Value)), {RED}, {INPUTBORDER})"
        if extra:
            p.update(extra)
        return ctl(gz, name, "text", IND, p)

    def combo(name, x, y, w, var, items, placeholder, multi=False, custom=False, h=32):
        if multi:
            default_sel = f'If(IsBlank({var}), Table(), ForAll(Split({var}, ", "), {{Value: Result}}))'
            on_change = f'Set({var}, Concat(Self.SelectedItems, Value, ", "))'
        else:
            default_sel = f'If(IsBlank({var}), Table(), Table({{Value: {var}}}))'
            on_change = f'Set({var}, Coalesce(Self.Selected.Value, ""))'
        p = {"BorderColor": INPUTBORDER, "BorderThickness": 1, "ChevronBackground": WHITE, "ChevronFill": MUTED,
             "Color": TEXT, "DefaultSelectedItems": default_sel, "Fill": WHITE, "Height": h,
             "InputTextPlaceholder": s(placeholder), "Items": items, "OnChange": on_change,
             "SelectMultiple": "true" if multi else "false", "Size": 12, "Width": w, "X": x, "Y": y}
        if custom:
            p["AllowCustomValue"] = "true"
        return ctl(gz, name, "combobox", IND, p)

    def date_input(name, x, y, w, var, extra_border=None):
        p = {"BorderColor": extra_border or INPUTBORDER, "BorderThickness": 1, "Color": TEXT,
             "DefaultDate": var, "Fill": WHITE, "Format": s("dd/mm/yyyy"), "Height": 32, "IconBackground": WHITE,
             "IconFill": MUTED, "OnChange": f"Set({var}, Self.SelectedDate)", "Size": 12, "Width": w, "X": x, "Y": y}
        return ctl(gz, name, "datepicker", IND, p)

    def card(name, x, y, w, h):
        return gr(name, x, y, w, h, WHITE, border=BORDER, bt=1)

    def section_header(key, title, y, text_w, stat):
        out = gl(f"Sec{key}Title", s(title), 32, y, text_w + 16, 28, size=20, color=NAVY, weight="Semibold")
        w = f'Switch({stat}.Text, "Complete", 74, "Needs review", 96, 85)'
        out += gb(f"Sec{key}Badge", f"{stat}.Text", 32 + text_w + 14, y + 3, w, 22,
                  by_status(stat, GREENBG, AMBERBG, GREYBG), by_status(stat, GREEN, AMBERTXT, MUTED),
                  border=by_status(stat, GREEN, AMBER, BORDER), radius=11, size=10,
                  extra={"DisplayMode": "DisplayMode.View"})
        return out

    def card_header(key, title, sub, x, y):
        out = gl(f"{key}Header", s(title), x, y, 600, 22, size=15, color=NAVY)
        if sub:
            out += helper(f"{key}Sub", sub, x, y + 24, 700)
        return out

    # ---- title block
    g += gl("PageTitle", s("New campaign request"), 32, 24, 700, 36, size=24, color=NAVY, weight="Bold")
    g += gl("PageSubtitle", s("Simplified request. Save a draft at any time and come back later."),
            32, 64, 700, 20, size=12, color=MUTED, weight="Normal")

    # ---- General (section y=116, card y=156 h=188)
    g += section_header("General", "General", 116, 77, "StatGeneral")
    g += card("GeneralCard", 32, 156, 1062, 188)
    g += field_label("LblTitle", "Campaign title", 52, 172, 400, True)
    g += text_input("InTitle", 52, 196, 501, "varTitle", "Name of the campaign")
    g += field_label("LblLead", "Campaign Lead", 573, 172, 400, True)
    g += combo("InLead", 573, 196, 501, "varLead", "Table({Value: User().FullName})", "Select the campaign lead", custom=True)
    g += field_label("LblDG", "DG / Unit", 52, 248, 300, True)
    g += combo("InDG", 52, 272, 327, "varDG", '["DG COMM, Unit B2"]', "Select or type a DG / Unit", custom=True)
    g += field_label("LblBudget", "Estimated budget (EUR)", 399, 248, 300)
    g += text_input("InBudget", 399, 272, 327, "varBudget", "e.g. 45,000", numeric=True)
    g += field_label("LblReqId", "Request ID", 746, 248, 300)
    g += text_input("InReqId", 746, 272, 327, "varRequestId", "", extra={
        "DisplayMode": "DisplayMode.Disabled", "DisabledFill": GREYBG, "DisabledColor": DISABLED,
        "DisabledBorderColor": BORDER, "OnChange": "false"})
    g += helper("HelpReqId", "Generated automatically", 746, 308, 327)

    # ---- Objectives & KPIs (section y=376)
    g += section_header("Obj", "Objectives & KPIs", 376, 167, "StatObjectives")
    g += card("ObjCard", 32, 416, 1062, 316)
    g += card_header("ObjCardTitle", "Campaign objective", None, 52, 432)
    g += field_label("LblObjective", "Primary objective", 52, 474, 400, True)
    g += combo("InObjective", 52, 498, 501,
               "varObjective",
               '["Engaged views", "Reach and impressions", "Video completions", "New subscribers", "Website traffic"]',
               "Select the primary objective")
    g += field_label("LblStart", "Start date", 573, 474, 240, True)
    g += date_input("InStart", 573, 498, 240, "varStartDate")
    g += field_label("LblEnd", "End date", 833, 474, 240, True)
    g += date_input("InEnd", 833, 498, 240, "varEndDate",
                    extra_border=f"If(Not(IsBlank(varEndDate)) And Not(IsBlank(varStartDate)) And varEndDate < varStartDate, {RED}, {INPUTBORDER})")
    g += field_label("LblOutcome", "Objective and expected outcome", 52, 550, 500, True)
    g += text_input("InOutcome", 52, 574, 1022, "varOutcome",
                    "Describe the objective and the outcome you expect", h=80, multiline=True)
    # always-on toggle (secondary objective)
    g += gb("SecondaryTrack", s(""), 52, 683, 40, 20, LIGHTBLUE, WHITE, radius=10,
            extra={"DisplayMode": "DisplayMode.View", "DisabledFill": LIGHTBLUE})
    g += gc("SecondaryThumb", 73, 686, 14, WHITE)
    g += gl("SecondaryText", s("New Subscribers as secondary objective"), 100, 674, 600, 20, size=12, color=TEXT, weight="Normal")
    g += helper("SecondaryHelp", "Always on. Required for all paid campaigns on the corporate YouTube channel.", 100, 696, 700)

    g += card("KpiCard", 32, 744, 1062, 318)
    g += card_header("KpiCardTitle", "KPI targets", "Numeric targets, compared with actuals in the final report", 52, 760)
    g += field_label("LblKpiViews", "Engaged views", 52, 820, 240, True)
    g += text_input("InKpiViews", 52, 844, 240, "varKpiViews", "e.g. 250,000", numeric=True)
    g += field_label("LblKpiVTR", "View through rate (%)", 312, 820, 240)
    g += text_input("InKpiVTR", 312, 844, 240, "varKpiVTR", "e.g. 35", numeric=True)
    g += field_label("LblKpiSubs", "New subscribers", 572, 820, 240, True)
    g += text_input("InKpiSubs", 572, 844, 240, "varKpiSubs", "e.g. 3,000", numeric=True)
    g += field_label("LblKpiCPS", "Cost per subscriber (EUR)", 832, 820, 240)
    g += text_input("InKpiCPS", 832, 844, 240, "varKpiCPS", "e.g. 0.80", numeric=True)
    g += field_label("LblKpiOther", "Other KPIs", 52, 896, 300)
    g += text_input("InKpiOther", 52, 920, 1022, "varKpiOther", "Add any other KPI and its target", h=64, multiline=True)
    g += gr("InfoBar", 52, 1004, 1022, 38, GREYBG, border=BORDER, bt=1)
    g += gc("InfoDot", 65, 1013, 20, BLUE)
    g += gl("InfoGlyph", s("i"), 65, 1013, 20, 20, size=11, color=WHITE, align="Center", valign="Middle")
    g += gl("InfoText", s("Targets are compared against actuals in the contractor's final report."),
            93, 1013, 900, 20, size=12, color=TEXT, weight="Normal")

    # ---- Audience (section y=1094, card y=1134 h=252)
    g += section_header("Aud", "Audience", 1094, 90, "StatAudience")
    g += card("AudCard", 32, 1134, 1062, 252)
    g += card_header("AudCardTitle", "Core audience", "Who the campaign is mainly aimed at", 52, 1150)
    g += field_label("LblAges", "Age ranges", 52, 1210, 300, True)
    g += combo("InAges", 52, 1234, 327, "varAges",
               '["13 to 17", "18 to 24", "25 to 34", "35 to 44", "45 to 54", "55 to 64", "65 and over"]',
               "Select age ranges", multi=True)
    g += field_label("LblGender", "Gender", 399, 1210, 300)
    g += ctl(gz, "InGender", "dropdown", IND, {
        "BorderColor": INPUTBORDER, "BorderThickness": 1, "ChevronBackground": WHITE, "ChevronFill": MUTED,
        "Color": TEXT, "Default": "varGender", "Fill": WHITE, "Height": 32, "Items": '["All", "Women", "Men"]',
        "OnChange": "Set(varGender, Self.Selected.Value)", "Size": 12, "Width": 327, "X": 399, "Y": 1234})
    g += field_label("LblLanguages", "Languages", 746, 1210, 300, True)
    langs = ('["Bulgarian", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish", "French", '
             '"German", "Greek", "Hungarian", "Irish", "Italian", "Latvian", "Lithuanian", "Maltese", "Polish", '
             '"Portuguese", "Romanian", "Slovak", "Slovenian", "Spanish", "Swedish"]')
    g += combo("InLanguages", 746, 1234, 327, "varLanguages", langs, "Select languages", multi=True)
    g += field_label("LblCountries", "Countries / regions", 52, 1286, 300, True)
    countries = ('["All EU27", "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", '
                 '"Finland", "France", "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", '
                 '"Luxembourg", "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", '
                 '"Spain", "Sweden"]')
    g += combo("InCountries", 52, 1310, 501, "varCountries", countries, "Select countries or regions", multi=True)
    g += field_label("LblInterests", "Interests, behaviours and mindset", 573, 1286, 400)
    g += text_input("InInterests", 573, 1310, 501, "varInterests",
                    "Who they are and what they care about", h=56, multiline=True)

    # ---- Attachments (section y=1418, card y=1458 h=254)
    g += section_header("Att", "Attachments", 1418, 125, "StatAttachments")
    g += card("AttCard", 32, 1458, 1062, 254)
    g += card_header("AttCardTitle", "Attachments",
                     "Creative brief, scripts, storyboards or media plan. Max 10 files, 10 MB each.", 52, 1474)
    g += ctl(gz, "InAttach", "attachments", IND, {
        "BorderColor": BORDER, "Height": 158, "MaxAttachmentSize": 10, "MaxAttachments": 10,
        "OnAddFile": "Set(varAttachCount, CountRows(Self.Attachments))",
        "OnRemoveFile": "Set(varAttachCount, CountRows(Self.Attachments))",
        "Width": 1022, "X": 52, "Y": 1534})

    # ---- Delivery (section y=1744, card y=1784 h=412)
    g += section_header("Del", "Delivery", 1744, 79, "StatDelivery")
    g += card("DelCard", 32, 1784, 1062, 412)
    g += card_header("DelCardTitle", "Delivery", "Setup, publication rules and final reporting", 52, 1800)
    g += gb("ContractorTrack", s(""), 52, 1860, 40, 20,
            "If(varContractorOn, " + BLUE + ", " + LIGHTBLUE + ")", WHITE, radius=10,
            onselect="Set(varContractorOn, Not(varContractorOn))",
            extra={"FocusedBorderThickness": 0})
    g += gc("ContractorThumb", "If(varContractorOn, 73, 55)", 1863, 14, WHITE,
            extra={"OnSelect": "Set(varContractorOn, Not(varContractorOn))"})
    g += gl("ContractorText", s("A contractor is engaged for setup, monitoring and the final report"),
            100, 1860, 700, 20, size=12, color=TEXT, weight="Normal")
    g += field_label("LblContractor", "Contractor", 52, 1900, 300)
    g += combo("InContractor", 52, 1924, 327, "varContractor", 'Filter(["x"], false)', "Select a contractor", custom=True)
    g += field_label("LblContractRef", "Contract reference", 399, 1900, 300)
    g += text_input("InContractRef", 399, 1924, 327, "varContractRef", "Framework and specific contract")
    g += field_label("LblReportDue", "Final report due", 746, 1900, 300)
    g += date_input("InReportDue", 746, 1924, 327, "varReportDue")
    for i, (nm, var, txt, y) in enumerate([
        ("Ack1", "varAck1", "I acknowledge campaign assets will be published as unlisted videos on the corporate channel", 1976),
        ("Ack2", "varAck2", "I acknowledge comments will be disabled on campaign assets for the duration of the campaign", 2016)]):
        g += ctl(gz, f"Chk{nm}", "checkbox.Checkbox", IND, {
            "CheckboxBackgroundFill": BLUE, "CheckboxBorderColor": INPUTBORDER, "CheckmarkFill": WHITE,
            "Color": TEXT, "Default": var, "Height": 24, "OnCheck": f"Set({var}, true)",
            "OnUncheck": f"Set({var}, false)", "Size": 12, "Text": s(txt), "Width": 1022, "X": 52, "Y": y})
    g += field_label("LblNotes", "Observations", 52, 2056, 300)
    g += text_input("InNotes", 52, 2080, 1022, "varNotes", "Add any notes for the reviewers or the contractor", h=96, multiline=True)

    # ---- Footer (y=2228)
    g += gr("FooterDivider", 32, 2228, 1062, 1, BORDER)
    g += gr("FooterErrBg", 32, 2249, 380, 38, REDBG, border=REDBORDER, bt=1, visible="Not(StatAll.Text = \"true\")")
    g += gc("FooterErrDot", 45, 2258, 20, RED, extra={"Visible": "Not(StatAll.Text = \"true\")"})
    g += gl("FooterErrGlyph", s("!"), 45, 2258, 20, 20, size=11, color=WHITE, align="Center", valign="Middle",
            visible="Not(StatAll.Text = \"true\")")
    g += gl("FooterErrText", '"Fill in " & StatMissing.Text & " before you can submit."', 73, 2258, 330, 20,
            size=12, color=RED, weight="Normal", visible="Not(StatAll.Text = \"true\")")
    g += gb("BtnCancel", s("Cancel"), 773, 2252, 61, 32, CLEAR, TEXT, hover=GREYBG,
            onselect=reset_block() + ";\nReset(InAttach);\nNotify(\"The form was cleared.\", NotificationType.Information)")
    g += gb("BtnDraft", s("Save as draft"), 842, 2252, 114, 32, WHITE, NAVY, border=INPUTBORDER, hover=GREYBG,
            onselect='Set(varStatus, "Draft");\n' + save_block("Draft") +
                     ';\nNotify("Draft " & varRequestId & " saved.", NotificationType.Success)')
    g += gb("BtnSubmit", s("Submit request"), 964, 2252, 130, 32, BLUE, WHITE, hover=NAVY,
            onselect=save_block("Submitted") +
                     ';\nNotify("Request " & varRequestId & " submitted.", NotificationType.Success);\n' +
                     reset_block() + ";\nReset(InAttach)",
            extra={"DisplayMode": 'If(StatAll.Text = "true", DisplayMode.Edit, DisplayMode.Disabled)',
                   "DisabledFill": BORDER, "DisabledColor": DISABLED, "DisabledBorderColor": BORDER})

    gallery = ctl(sc, "MainScroll", "gallery", 4, {
        "Fill": BG, "Height": 712, "Items": "[{id: 1}]", "Layout": "Layout.Vertical",
        "TemplatePadding": 0, "TemplateSize": 2319, "Width": 1126, "X": 240, "Y": 56}, children=g)

    head = ["CampaignRequestScreen As screen:", f"    Fill: ={BG}", ""]
    return "\n".join(head + body + gallery)


def main():
    os.makedirs(os.path.join(OUT, "Src"), exist_ok=True)
    write_app()
    text = build_screen().rstrip() + "\n"
    with open(os.path.join(OUT, "Src", "CampaignRequestScreen.fx.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("written", len(text.splitlines()), "lines")


main()
