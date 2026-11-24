from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

from src import atlas, explorer, lab, pipeline
from src.i18n import APP_NAME, AUTHOR_ID, AUTHOR_NAME, STACK, TEXT

FILTER_KEYS = ("category", "language", "sentiment", "query", "sort")
DEFAULT_UI = {"mode": "pred", "stat": "mean", "category": [], "language": [], "sentiment": [], "query": "", "sort": "recent", "page": 0, "playground": None}
ROLE_ORDER = ["text", "label", "category", "language", "time", "likes", "comments", "shares"]

app = Dash(__name__, title=f"{APP_NAME} | Sentiment Intelligence", update_title=None, suppress_callback_exceptions=True)
server = app.server


def number(value, lang):
    text = f"{int(value):,}"
    return text.replace(",", ".") if lang == "vi" else text


def percent(value, lang):
    text = f"{value * 100:.1f}%"
    return text.replace(".", ",") if lang == "vi" else text


def unlocked_step(raw, report):
    if report:
        return 5
    if raw and not raw.get("error"):
        return 2
    return 1


def completed_step(raw, report):
    if report:
        return 2
    if raw and not raw.get("error"):
        return 1
    return 0


def build_nav(lang):
    anchors = ["#journey", "#workspace", "#about"]
    return [html.A(label, href=href, className="nav-link") for label, href in zip(TEXT[lang]["nav"], anchors)]


def build_landing(lang):
    t = TEXT[lang]
    hero = html.Section(
        className="hero reveal",
        children=[
            html.Div(t["badge"], className="hero-badge"),
            html.H1([html.Span(t["title_1"], className="title-line"), html.Span(t["title_2"], className="title-line title-gradient")], className="hero-title"),
            html.P(t["subtitle"], className="hero-sub"),
            html.Div([html.A(t["cta"], href="#workspace", className="btn btn-primary"), html.A(t["cta_secondary"], href="#journey", className="btn btn-ghost")], className="hero-actions"),
            html.Div([html.Div([html.Div(value, className="stat-value"), html.Div(label, className="stat-label")], className="stat") for value, label in t["stats"]], className="hero-stats"),
        ],
    )
    journey = html.Section(
        id="journey",
        className="section reveal",
        children=[
            html.H2(t["journey_title"], className="section-title"),
            html.P(t["journey_sub"], className="section-sub"),
            html.Div(
                [
                    html.Div(
                        [html.Div([html.Span(num, className="step-number"), html.Span(icon, className="step-icon")], className="step-top"), html.H3(title, className="step-title"), html.P(desc, className="step-desc")],
                        className="step-card tilt",
                    )
                    for num, icon, title, desc in t["steps"]
                ],
                className="step-grid",
            ),
        ],
    )
    return [hero, journey]


def build_footer(lang):
    t = TEXT[lang]
    return html.Div(
        className="footer-inner",
        id="about",
        children=[
            html.Div([html.Div([html.Span(className="brand-mark"), html.Span(APP_NAME, className="brand-name")], className="brand"), html.P(t["footer_about"], className="footer-text")], className="footer-col"),
            html.Div([html.Div(t["footer_author"], className="footer-head"), html.P(AUTHOR_NAME, className="footer-text strong"), html.P(AUTHOR_ID, className="footer-text")], className="footer-col"),
            html.Div([html.Div(t["footer_stack"], className="footer-head"), html.Div([html.Span(item, className="chip") for item in STACK], className="chips")], className="footer-col"),
            html.Div(f"© 2026 {APP_NAME}. {t['rights']}", className="footer-bottom"),
        ],
    )


def build_stepper(lang, step, unlocked, completed):
    items = []
    for index, (num, icon, title, _) in enumerate(TEXT[lang]["steps"], 1):
        state = ["step-chip"]
        if index == step:
            state.append("active")
        if index <= completed:
            state.append("done")
        if index > unlocked:
            state.append("locked")
        badge = "✓" if index <= completed else ("🔒" if index > unlocked else icon)
        items.append(
            html.Button(
                [html.Span(badge, className="chip-badge"), html.Span([html.Span(num, className="chip-num"), html.Span(title, className="chip-title")], className="chip-text")],
                id={"type": "step-btn", "index": index},
                className=" ".join(state),
                disabled=index > unlocked,
                n_clicks=0,
            )
        )
    return items


def build_nav_buttons(lang, step, unlocked):
    ws = TEXT[lang]["ws"]
    return [
        html.Button(ws["back"], id={"type": "nav-btn", "index": "prev"}, className="btn btn-ghost btn-sm", disabled=step <= 1, n_clicks=0),
        html.Button(ws["next"], id={"type": "nav-btn", "index": "next"}, className="btn btn-primary btn-sm", disabled=step >= 5 or step + 1 > unlocked, n_clicks=0),
    ]


def role_chips(lang, mapping):
    ws = TEXT[lang]["ws"]
    chips = []
    for role in ROLE_ORDER:
        column = mapping.get(role)
        chips.append(
            html.Div(
                [html.Span("✓" if column else "–", className="role-mark"), html.Span(ws["roles"][role], className="role-name"), html.Span(column if column else ws["missing"], className="role-col")],
                className="role-chip found" if column else "role-chip",
            )
        )
    return html.Div(chips, className="role-grid")


def preview_table(preview):
    head = html.Thead(html.Tr([html.Th(col) for col in preview["columns"]]))
    body = html.Tbody([html.Tr([html.Td(cell) for cell in row]) for row in preview["rows"]])
    return html.Div(html.Table([head, body], className="data-table compact"), className="table-wrap")


def panel_launchpad(lang, raw):
    ws = TEXT[lang]["ws"]
    sources = html.Div(
        className="source-grid",
        children=[
            html.Div(
                [
                    html.Div("🧬", className="source-icon"),
                    html.H3(ws["sample_title"], className="source-title"),
                    html.P(ws["sample_desc"], className="source-desc"),
                    html.Button(ws["sample_btn"], id={"type": "act-btn", "index": "sample"}, className="btn btn-primary", n_clicks=0),
                ],
                className="source-card tilt",
            ),
            html.Div(
                [
                    html.Div("☁️", className="source-icon"),
                    html.H3(ws["upload_title"], className="source-title"),
                    dcc.Upload(
                        id={"type": "upload", "index": "csv"},
                        accept=".csv",
                        multiple=False,
                        max_size=25_000_000,
                        className="upload-zone",
                        children=[html.Div(ws["upload_drop"], className="upload-main"), html.Div(ws["upload_or"], className="upload-sub")],
                    ),
                    html.P(ws["upload_hint"], className="source-hint"),
                ],
                className="source-card tilt",
            ),
        ],
    )
    blocks = [html.Div([html.H2(ws["s1_title"], className="panel-title"), html.P(ws["s1_sub"], className="panel-sub")], className="panel-head"), sources]
    if raw and raw.get("error"):
        blocks.append(html.Div([html.Span("⚠️"), html.Span(ws["err_no_text"] if raw["error"] == "no_text" else ws["err_read"])], className="notice notice-error"))
    elif raw:
        name = ws["source_sample"] if raw["source"] == "sample" else raw["name"]
        blocks.append(
            html.Div(
                className="loaded-card",
                children=[
                    html.Div(
                        [
                            html.Span("✅", className="loaded-icon"),
                            html.Div([html.Div(ws["loaded_title"], className="loaded-title"), html.Div(name, className="loaded-name")]),
                            html.Div([html.Span(f"{number(raw['rows'], lang)} {ws['rows']}", className="chip"), html.Span(f"{number(raw['cols'], lang)} {ws['cols']}", className="chip")], className="loaded-chips"),
                        ],
                        className="loaded-head",
                    ),
                    html.Div(ws["roles_title"], className="mini-head"),
                    role_chips(lang, raw["mapping"]),
                    html.Div(ws["preview"], className="mini-head"),
                    preview_table(raw["preview"]),
                ],
            )
        )
    return blocks


def kpi_tile(label, value, accent="violet"):
    return html.Div([html.Div(value, className="kpi-value"), html.Div(label, className="kpi-label")], className=f"kpi-tile tilt kpi-{accent}")


def panel_refinery(lang, raw, report):
    ws = TEXT[lang]["ws"]
    head = html.Div([html.H2(ws["s2_title"], className="panel-title"), html.P(ws["s2_sub"], className="panel-sub")], className="panel-head")
    if not raw or raw.get("error"):
        return [head]
    stages = html.Div(
        [html.Div([html.Div(icon, className="stage-icon"), html.H3(title, className="stage-title"), html.P(desc, className="stage-desc")], className="stage-card") for icon, title, desc in ws["stages"]],
        className="stage-grid",
    )
    if not report:
        return [head, stages, html.Div(html.Button(ws["run"], id={"type": "act-btn", "index": "run"}, className="btn btn-primary btn-lg", n_clicks=0), className="center-row")]
    period = f"{report['period'][0]}  →  {report['period'][1]}" if report["period"] else "–"
    tiles = [
        kpi_tile(ws["kpi_in"], number(report["rows_in"], lang), "violet"),
        kpi_tile(ws["kpi_out"], number(report["rows_out"], lang), "mint"),
        kpi_tile(ws["kpi_dup"], number(report["duplicates"], lang), "pink"),
        kpi_tile(ws["kpi_missing"], number(report["missing_text"], lang), "pink"),
        kpi_tile(ws["kpi_empty"], number(report["empty"], lang), "amber"),
        kpi_tile(ws["kpi_cat"], number(report["n_categories"], lang), "cyan"),
        kpi_tile(ws["kpi_lang"], number(report["n_languages"], lang), "cyan"),
        kpi_tile(ws["kpi_period"], period, "violet wide"),
    ]
    if report["has_label"]:
        tiles.insert(5, kpi_tile(ws["kpi_invalid"], number(report["invalid_labels"], lang), "amber"))
    sample_rows = [html.Tr([html.Td(item["before"]), html.Td(item["after"], className="cell-after")]) for item in report["samples"]]
    sample_table = html.Div(html.Table([html.Thead(html.Tr([html.Th(ws["before"]), html.Th(ws["after"])])), html.Tbody(sample_rows)], className="data-table"), className="table-wrap")
    blocks = [
        head,
        html.Div([html.Span("🎉"), html.Span(ws["ready"])], className="notice notice-success"),
        html.Div(tiles, className="kpi-grid"),
    ]
    if report["agreement"] is not None:
        blocks.append(
            html.Div(
                [html.Div(percent(report["agreement"], lang), className="agree-value"), html.Div([html.Div(ws["agree_title"], className="agree-title"), html.P(ws["agree_note"], className="agree-note")])],
                className="agree-card",
            )
        )
    else:
        blocks.append(html.Div([html.Span("ℹ️"), html.Span(ws["no_label"])], className="notice notice-info"))
    blocks += [html.Div(ws["samples"], className="mini-head"), sample_table]
    return blocks


def panel_coming(lang, step, report):
    ws = TEXT[lang]["ws"]
    num, icon, title, desc = TEXT[lang]["steps"][step - 1]
    rows = number(report["rows_out"], lang) if report else "0"
    return [
        html.Div(
            className="coming-card",
            children=[
                html.Div(icon, className="coming-icon"),
                html.H2(title, className="panel-title"),
                html.P(desc, className="panel-sub"),
                html.Div(ws["coming_title"], className="coming-badge"),
                html.P(ws["coming_sub"], className="source-hint"),
                html.Div([html.Span("✓"), html.Span(f"{ws['data_ready']}: {rows} {ws['posts']}")], className="coming-ready"),
            ],
        )
    ]


app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(className="aurora"),
        html.Div(className="stars"),
        html.Div(className="orb orb-a"),
        html.Div(className="orb orb-b"),
        html.Div(className="orb orb-c"),
        dcc.Store(id="step-store", data=1),
        dcc.Store(id="raw-store"),
        dcc.Store(id="clean-store"),
        dcc.Store(id="report-store"),
        dcc.Store(id="ui-store", data=dict(DEFAULT_UI)),
        dcc.Download(id="download-data"),
        html.Header(
            className="site-header",
            children=[
                html.A([html.Span(className="brand-mark"), html.Div([html.Span(APP_NAME, className="brand-name"), html.Span(id="brand-tagline", className="brand-tagline")], className="brand-text")], href="#", className="brand"),
                html.Nav(id="nav-links", className="nav"),
                dcc.RadioItems(
                    id="lang-switch",
                    options=[{"label": "VI", "value": "vi"}, {"label": "EN", "value": "en"}],
                    value="vi",
                    className="lang-pill",
                    persistence=True,
                    persistence_type="local",
                ),
            ],
        ),
        html.Main(id="landing", className="page-body"),
        html.Section(
            id="workspace",
            className="workspace",
            children=[
                html.Div(id="workspace-head", className="workspace-head"),
                html.Div(id="stepper", className="stepper"),
                dcc.Loading(
                    type="circle",
                    color="#7c5cff",
                    children=html.Div(id="step-panel", className="step-panel"),
                ),
                html.Div(id="step-nav", className="step-nav"),
            ],
        ),
        html.Footer(id="site-footer", className="site-footer"),
    ],
)


@app.callback(
    Output("brand-tagline", "children"),
    Output("nav-links", "children"),
    Output("landing", "children"),
    Output("site-footer", "children"),
    Output("workspace-head", "children"),
    Input("lang-switch", "value"),
)
def render_language(lang):
    lang = lang if lang in TEXT else "vi"
    ws = TEXT[lang]["ws"]
    head = [html.H2(ws["title"], className="section-title"), html.P(ws["sub"], className="section-sub")]
    return TEXT[lang]["tagline"], build_nav(lang), build_landing(lang), build_footer(lang), head


@app.callback(
    Output("stepper", "children"),
    Output("step-panel", "children"),
    Output("step-nav", "children"),
    Input("lang-switch", "value"),
    Input("step-store", "data"),
    Input("raw-store", "data"),
    Input("report-store", "data"),
    Input("ui-store", "data"),
    State("clean-store", "data"),
)
def render_workspace(lang, step, raw, report, ui, clean):
    lang = lang if lang in TEXT else "vi"
    step = step or 1
    unlocked = unlocked_step(raw, report)
    completed = completed_step(raw, report)
    if step == 1:
        panel = panel_launchpad(lang, raw)
    elif step == 2:
        panel = panel_refinery(lang, raw, report)
    elif step == 3 and clean and report:
        panel = atlas.build_panel(lang, pipeline.unpack_clean(clean), report, (ui or DEFAULT_UI).get("mode", "pred"))
    elif step == 4 and clean and report:
        panel = lab.build_panel(lang, pipeline.unpack_clean(clean), report, ui or DEFAULT_UI)
    elif step == 5 and clean and report:
        panel = explorer.build_panel(lang, pipeline.unpack_clean(clean), report, ui or DEFAULT_UI)
    else:
        panel = panel_coming(lang, step, report)
    return build_stepper(lang, step, unlocked, completed), panel, build_nav_buttons(lang, step, unlocked)


@app.callback(
    Output("step-store", "data"),
    Output("raw-store", "data"),
    Output("clean-store", "data"),
    Output("report-store", "data"),
    Output("ui-store", "data"),
    Input({"type": "step-btn", "index": ALL}, "n_clicks"),
    Input({"type": "nav-btn", "index": ALL}, "n_clicks"),
    Input({"type": "act-btn", "index": ALL}, "n_clicks"),
    Input({"type": "upload", "index": ALL}, "contents"),
    Input({"type": "pref", "index": ALL}, "value"),
    State({"type": "upload", "index": ALL}, "filename"),
    State({"type": "field", "index": ALL}, "value"),
    State("step-store", "data"),
    State("raw-store", "data"),
    State("report-store", "data"),
    State("ui-store", "data"),
    prevent_initial_call=True,
)
def controller(step_clicks, nav_clicks, act_clicks, upload_contents, pref_values, upload_names, field_values, step, raw, report, ui):
    trigger = ctx.triggered_id
    if trigger is None:
        raise PreventUpdate
    value = ctx.triggered[0]["value"]

    if trigger["type"] == "pref":
        current = dict(ui or DEFAULT_UI)
        if current.get(trigger["index"]) == value:
            raise PreventUpdate
        current[trigger["index"]] = value
        if trigger["index"] in FILTER_KEYS:
            current["page"] = 0
        return no_update, no_update, no_update, no_update, current

    if not value:
        raise PreventUpdate
    step = step or 1
    unlocked = unlocked_step(raw, report)

    if trigger["type"] in ("step-btn", "nav-btn"):
        if trigger["type"] == "step-btn":
            target = trigger["index"]
        else:
            target = step + (1 if trigger["index"] == "next" else -1)
        if 1 <= target <= unlocked and target != step:
            return target, no_update, no_update, no_update, no_update
        raise PreventUpdate

    if trigger["type"] == "act-btn" and trigger["index"] == "sample":
        return 1, pipeline.pack_raw(pipeline.load_sample_raw(), "sample", None), None, None, dict(DEFAULT_UI)

    if trigger["type"] == "upload":
        filename = upload_names[0] if upload_names else None
        try:
            packed = pipeline.pack_raw(pipeline.parse_upload(upload_contents[0]), "upload", filename)
        except Exception:
            packed = {"source": "upload", "name": filename, "error": "read_error"}
        return 1, packed, None, None, dict(DEFAULT_UI)

    if trigger["type"] == "act-btn" and trigger["index"] == "run" and raw and not raw.get("error"):
        clean, new_report = pipeline.refine(pipeline.unpack_raw(raw), raw["mapping"])
        return 2, no_update, pipeline.pack_clean(clean), new_report, dict(DEFAULT_UI)

    if trigger["type"] == "act-btn":
        current = dict(ui or DEFAULT_UI)
        if trigger["index"] == "reset":
            for key in FILTER_KEYS:
                current[key] = [] if isinstance(DEFAULT_UI[key], list) else DEFAULT_UI[key]
            current["page"] = 0
            return no_update, no_update, no_update, no_update, current
        if trigger["index"] in ("page-prev", "page-next"):
            current["page"] = max(0, int(current.get("page", 0) or 0) + (1 if trigger["index"] == "page-next" else -1))
            return no_update, no_update, no_update, no_update, current
        if trigger["index"] == "predict":
            text = field_values[0] if field_values else ""
            current["playground"] = explorer.predict_text(text) or "empty"
            return no_update, no_update, no_update, no_update, current

    raise PreventUpdate


@app.callback(
    Output("download-data", "data"),
    Input({"type": "act-btn", "index": ALL}, "n_clicks"),
    State("clean-store", "data"),
    State("report-store", "data"),
    State("ui-store", "data"),
    prevent_initial_call=True,
)
def download_filtered(n_clicks, clean, report, ui):
    trigger = ctx.triggered_id
    if trigger is None or trigger["index"] != "download" or not ctx.triggered[0]["value"] or not clean:
        raise PreventUpdate
    frame = explorer.filter_frame(pipeline.unpack_clean(clean), ui or DEFAULT_UI, bool((report or {}).get("has_label")))
    return dcc.send_data_frame(explorer.export_frame(frame).to_csv, "sentiverse_bai_dang_da_loc.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)