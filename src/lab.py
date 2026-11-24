import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from plotly.subplots import make_subplots
from scipy.stats import kruskal

from src.atlas import COLORS, ORDER, TEXT as ATLAS_TEXT, base_layout, whole

METRICS = ["Likes", "Comments", "Shares"]
ROLE_OF = {"Likes": "likes", "Comments": "comments", "Shares": "shares"}
STATS = ["mean", "median", "total"]

TEXT = {
    "vi": {
        "title": "Phòng thí nghiệm tương tác",
        "sub": "Likes, Comments và Shares thay đổi ra sao theo từng nhóm cảm xúc.",
        "stats": {"mean": "Trung bình", "median": "Trung vị", "total": "Tổng"},
        "best": "{metric} cao nhất",
        "table_title": "Bảng tương tác theo nhóm cảm xúc",
        "col_group": "Nhóm cảm xúc",
        "col_posts": "Số bài",
        "bars_title": "So sánh từng chỉ số giữa ba nhóm cảm xúc",
        "radar_title": "Chỉ số tương tác so với mức trung bình toàn bộ (= 100)",
        "radar_overall": "Toàn bộ = 100",
        "test_title": "Kiểm định khác biệt giữa các nhóm",
        "test_sub": "Kruskal-Wallis, mức ý nghĩa 5%",
        "sig_yes": "Khác biệt có ý nghĩa thống kê",
        "sig_no": "Chưa có ý nghĩa thống kê",
        "sig_na": "Không đủ dữ liệu",
        "note": "Trung bình dễ bị kéo lệch bởi vài bài có tương tác rất cao, hãy đối chiếu thêm với trung vị. Khác biệt giữa các nhóm chỉ đáng tin khi kiểm định cho thấy có ý nghĩa thống kê.",
        "no_engagement": "Tệp dữ liệu không có cột Likes, Comments hoặc Shares nên chưa thể phân tích tương tác.",
        "per_post": "mỗi bài",
    },
    "en": {
        "title": "Engagement Lab",
        "sub": "How Likes, Comments and Shares change across each sentiment group.",
        "stats": {"mean": "Mean", "median": "Median", "total": "Total"},
        "best": "Highest {metric}",
        "table_title": "Engagement by sentiment group",
        "col_group": "Sentiment group",
        "col_posts": "Posts",
        "bars_title": "Each metric compared across the three sentiment groups",
        "radar_title": "Engagement index versus the overall average (= 100)",
        "radar_overall": "Overall = 100",
        "test_title": "Testing differences between groups",
        "test_sub": "Kruskal-Wallis, 5% significance level",
        "sig_yes": "Statistically significant difference",
        "sig_no": "Not statistically significant",
        "sig_na": "Not enough data",
        "note": "The mean can be pulled by a few posts with very high engagement, so compare it with the median. Differences between groups are only reliable when the test shows statistical significance.",
        "no_engagement": "The file has no Likes, Comments or Shares column, so engagement cannot be analysed yet.",
        "per_post": "per post",
    },
}


def swap_separators(text):
    return text.translate(str.maketrans(",.", ".,"))


def format_value(value, stat, lang):
    if stat == "total":
        return whole(value, lang)
    text = f"{value:,.1f}"
    return swap_separators(text) if lang == "vi" else text


def p_label_text(value, lang):
    if value < 0.001:
        return "p < 0,001" if lang == "vi" else "p < 0.001"
    text = f"{value:.3f}"
    return f"p = {text.replace('.', ',')}" if lang == "vi" else f"p = {text}"


def hex_rgba(color, alpha):
    color = color.lstrip("#")
    r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def group_table(frame, column, metrics, stat):
    grouped = frame.groupby(column)[metrics]
    table = {"mean": grouped.mean, "median": grouped.median, "total": grouped.sum}[stat]()
    return table.reindex(ORDER).fillna(0)


def significance(frame, column, metric):
    groups = [g[metric].to_numpy() for _, g in frame.groupby(column) if len(g) > 1]
    if len(groups) < 2 or all(np.ptp(g) == 0 for g in groups):
        return None
    try:
        return float(kruskal(*groups).pvalue)
    except ValueError:
        return None


def bars_figure(table, metrics, stat, lang):
    fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=metrics, horizontal_spacing=0.08)
    for position, metric in enumerate(metrics, 1):
        values = [float(table.loc[k, metric]) for k in ORDER]
        fig.add_trace(
            go.Bar(
                x=ORDER,
                y=values,
                marker={"color": [COLORS[k] for k in ORDER], "line": {"width": 0}},
                text=[f"<b>{format_value(v, stat, lang)}</b>" for v in values],
                textposition="outside",
                textfont={"size": 13},
                cliponaxis=False,
                hovertemplate="%{x}<br>%{y:,.1f}<extra></extra>",
            ),
            row=1,
            col=position,
        )
        fig.update_yaxes(range=[0, max(values) * 1.28 if max(values) else 1], gridcolor="rgba(255,255,255,0.08)", zeroline=False, tickfont={"color": "#b2afd9", "size": 11}, row=1, col=position)
        fig.update_xaxes(tickfont={"size": 12}, row=1, col=position)
    fig.update_layout(**base_layout(lang, showlegend=False, bargap=0.35, margin={"l": 20, "r": 20, "t": 50, "b": 20}))
    fig.update_annotations(font={"size": 15, "color": "#e9e6ff"})
    return fig


def radar_figure(index_table, metrics, lang):
    t = TEXT[lang]
    theta = metrics + [metrics[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[100] * len(theta), theta=theta, mode="lines", line={"color": "rgba(255,255,255,0.5)", "dash": "dot", "width": 1.5}, name=t["radar_overall"], hoverinfo="skip"))
    for key in ORDER:
        values = [float(index_table.loc[key, m]) for m in metrics]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=theta,
                fill="toself",
                fillcolor=hex_rgba(COLORS[key], 0.18),
                line={"color": COLORS[key], "width": 2.5},
                marker={"size": 7},
                name=key,
                hovertemplate="%{theta}: %{r:.0f}<extra>" + key + "</extra>",
            )
        )
    top = max(130.0, float(index_table[metrics].to_numpy().max()) * 1.1)
    fig.update_layout(
        **base_layout(
            lang,
            margin={"l": 50, "r": 50, "t": 30, "b": 40},
            polar={
                "bgcolor": "rgba(0,0,0,0)",
                "radialaxis": {"range": [0, top], "gridcolor": "rgba(255,255,255,0.14)", "linecolor": "rgba(255,255,255,0.14)", "tickfont": {"size": 10, "color": "#b2afd9"}},
                "angularaxis": {"gridcolor": "rgba(255,255,255,0.14)", "linecolor": "rgba(255,255,255,0.2)", "tickfont": {"size": 13}},
            },
            legend={"orientation": "h", "y": -0.08, "x": 0.5, "xanchor": "center", "font": {"size": 12}},
        )
    )
    return fig


def toggle(id_index, options, value):
    return dcc.RadioItems(id={"type": "pref", "index": id_index}, options=options, value=value, className="lang-pill mode-pill")


def build_panel(lang, clean, report, ui):
    t = TEXT[lang]
    atlas_t = ATLAS_TEXT[lang]
    ui = ui or {}
    mapping = report.get("mapping", {})
    metrics = [m for m in METRICS if mapping.get(ROLE_OF[m])]
    stat = ui.get("stat", "mean") if ui.get("stat", "mean") in STATS else "mean"
    has_label = bool(report.get("has_label"))
    mode = "true" if (ui.get("mode") == "true" and has_label) else "pred"
    column = "Cam_xuc_that" if mode == "true" else "Cam_xuc_du_doan"

    controls = [toggle("stat", [{"label": t["stats"][s], "value": s} for s in STATS], stat)]
    if has_label:
        controls.append(toggle("mode", [{"label": atlas_t["mode_pred"], "value": "pred"}, {"label": atlas_t["mode_true"], "value": "true"}], mode))
    head = html.Div([html.Div([html.H2(t["title"], className="panel-title"), html.P(t["sub"], className="panel-sub")]), html.Div(controls, className="control-row")], className="atlas-head")
    if not metrics:
        return [head, html.Div([html.Span("ℹ️"), html.Span(t["no_engagement"])], className="notice notice-info")]

    frame = clean[clean[column].notna()]
    table = group_table(frame, column, metrics, stat)
    mean_table = group_table(frame, column, metrics, "mean")
    overall = frame[metrics].mean()
    index_table = mean_table.copy()
    for metric in metrics:
        index_table[metric] = mean_table[metric] / overall[metric] * 100 if overall[metric] else 100.0
    counts = frame[column].value_counts().reindex(ORDER, fill_value=0)

    chips = []
    for metric in metrics:
        best = table[metric].idxmax()
        chips.append(
            html.Div(
                [
                    html.Div(t["best"].format(metric=metric), className="best-label"),
                    html.Div([html.Span(className=f"dot dot-{best.lower()}"), html.Span(best, className="best-name", style={"color": COLORS[best]})], className="best-group"),
                    html.Div(f"{format_value(table.loc[best, metric], stat, lang)}" + ("" if stat == "total" else f" {t['per_post']}"), className="best-value"),
                ],
                className="best-chip tilt",
            )
        )

    maxes = {m: float(table[m].max()) for m in metrics}
    header = html.Thead(html.Tr([html.Th(t["col_group"]), html.Th(t["col_posts"])] + [html.Th(m) for m in metrics]))
    body_rows = []
    for key in ORDER:
        cells = [
            html.Td([html.Span(className=f"dot dot-{key.lower()}"), html.Span(atlas_t["names"][key])], className="group-cell"),
            html.Td(whole(counts[key], lang)),
        ]
        for metric in metrics:
            share = (float(table.loc[key, metric]) / maxes[metric] * 100) if maxes[metric] else 0
            cells.append(html.Td(html.Span(format_value(float(table.loc[key, metric]), stat, lang), className="heat-text"), className="heat-cell", style={"--w": f"{share:.0f}%"}))
        body_rows.append(html.Tr(cells))
    table_card = html.Div(
        [html.Div(f"{t['table_title']} · {t['stats'][stat]}", className="chart-title"), html.Div(html.Table([header, html.Tbody(body_rows)], className="data-table lab-table"), className="table-wrap")],
        className="chart-card",
    )
    bars_card = html.Div([html.Div(t["bars_title"] + f" · {t['stats'][stat]}", className="chart-title"), dcc.Graph(figure=bars_figure(table, metrics, stat, lang), config={"displayModeBar": False}, style={"height": "360px"})], className="chart-card")

    second_row = []
    if len(metrics) >= 3:
        second_row.append(html.Div([html.Div(t["radar_title"], className="chart-title"), dcc.Graph(figure=radar_figure(index_table, metrics, lang), config={"displayModeBar": False}, style={"height": "380px"})], className="chart-card"))
    test_rows = []
    for metric in metrics:
        p_value = significance(frame, column, metric)
        if p_value is None:
            verdict, css, p_label = t["sig_na"], "sig-na", "–"
        elif p_value < 0.05:
            verdict, css, p_label = t["sig_yes"], "sig-yes", p_label_text(p_value, lang)
        else:
            verdict, css, p_label = t["sig_no"], "sig-no", p_label_text(p_value, lang)
        test_rows.append(html.Div([html.Div(metric, className="test-metric"), html.Div(p_label, className="test-p"), html.Div(verdict, className=f"test-verdict {css}")], className="test-row"))
    second_row.append(
        html.Div(
            [html.Div(t["test_title"], className="chart-title"), html.Div(t["test_sub"], className="chart-subtitle"), html.Div(test_rows, className="test-list"), html.P(t["note"], className="chart-note")],
            className="chart-card",
        )
    )
    return [head, html.Div(chips, className="best-grid"), table_card, bars_card, html.Div(second_row, className="chart-grid")]