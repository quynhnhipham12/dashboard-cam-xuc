import plotly.graph_objects as go
from dash import dcc, html

ORDER = ["Positive", "Neutral", "Negative"]
COLORS = {"Positive": "#38f2b3", "Neutral": "#8da2ff", "Negative": "#ff5c8a"}
MODEL_ACCURACY = 0.5165
BASELINE_ACCURACY = 0.4204
FONT = {"family": "Be Vietnam Pro, -apple-system, Segoe UI, Roboto, sans-serif", "color": "#e9e6ff"}

TEXT = {
    "vi": {
        "title": "Bản đồ cảm xúc",
        "sub": "Toàn cảnh cảm xúc của cộng đồng qua từng bài đăng.",
        "mode_pred": "Nhãn dự đoán",
        "mode_true": "Nhãn gốc",
        "total": "Tổng số bài đăng",
        "unit": "bài đăng",
        "names": {"Positive": "Positive · Tích cực", "Neutral": "Neutral · Trung lập", "Negative": "Negative · Tiêu cực"},
        "dominant": "Cảm xúc chủ đạo",
        "dominant_tail": "chiếm {pct} số bài đăng",
        "avg_conf": "Độ tin cậy trung bình của mô hình",
        "donut_title": "Tỷ trọng ba nhóm cảm xúc",
        "bar_title": "Số lượng bài đăng theo nhóm cảm xúc",
        "note_pred": "Số liệu theo nhãn dự đoán của mô hình Naive Bayes. Độ chính xác trên tập kiểm thử là {acc}, cao hơn mức {base} nếu luôn đoán lớp đa số.",
        "note_true": "Số liệu theo nhãn gốc của bộ dữ liệu. Nhãn gốc có nhiều nhiễu: cùng một nội dung có thể mang các nhãn khác nhau.",
        "empty": "Chưa có dữ liệu để hiển thị.",
    },
    "en": {
        "title": "Sentiment Atlas",
        "sub": "A panoramic view of community sentiment across every post.",
        "mode_pred": "Predicted label",
        "mode_true": "Original label",
        "total": "Total posts",
        "unit": "posts",
        "names": {"Positive": "Positive", "Neutral": "Neutral", "Negative": "Negative"},
        "dominant": "Dominant sentiment",
        "dominant_tail": "accounts for {pct} of all posts",
        "avg_conf": "Average model confidence",
        "donut_title": "Share of the three sentiment groups",
        "bar_title": "Number of posts by sentiment group",
        "note_pred": "Figures use the label predicted by the Naive Bayes model. Its test accuracy is {acc}, above the {base} obtained by always guessing the majority class.",
        "note_true": "Figures use the original labels of the dataset. These labels are noisy: the same content can carry different labels.",
        "empty": "There is no data to display yet.",
    },
}


def whole(value, lang):
    text = f"{int(value):,}"
    return text.replace(",", ".") if lang == "vi" else text


def pct_text(value, lang, decimals=1):
    text = f"{value * 100:.{decimals}f}%"
    return text.replace(".", ",") if lang == "vi" else text


def countup(display, target, lang, decimals=0, suffix="", class_name="countup"):
    attrs = {"data-target": str(target), "data-decimals": str(decimals), "data-suffix": suffix, "data-locale": lang}
    return html.Span(display, className=class_name, **attrs)


def base_layout(lang, **extra):
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": FONT,
        "margin": {"l": 20, "r": 20, "t": 20, "b": 20},
        "separators": ",." if lang == "vi" else ".,",
        **extra,
    }


def donut_figure(counts, total, lang):
    t = TEXT[lang]
    fig = go.Figure(
        go.Pie(
            labels=ORDER,
            values=[int(counts[k]) for k in ORDER],
            hole=0.58,
            sort=False,
            direction="clockwise",
            pull=[0.025, 0.025, 0.025],
            marker={"colors": [COLORS[k] for k in ORDER], "line": {"color": "#0b0a26", "width": 4}},
            textinfo="percent",
            insidetextorientation="horizontal",
            textfont={"size": 15, "color": "#06121a"},
            hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(
        **base_layout(
            lang,
            showlegend=True,
            legend={"orientation": "h", "y": -0.06, "x": 0.5, "xanchor": "center", "font": {"size": 13}},
            annotations=[{"text": f"<b>{whole(total, lang)}</b><br><span style='font-size:13px;color:#b2afd9'>{t['unit']}</span>", "x": 0.5, "y": 0.5, "showarrow": False, "font": {"size": 30}}],
        )
    )
    return fig


def bar_figure(counts, shares, lang):
    values = [int(counts[k]) for k in ORDER]
    fig = go.Figure(
        go.Bar(
            x=ORDER,
            y=values,
            marker={"color": [COLORS[k] for k in ORDER], "line": {"width": 0}},
            text=[f"<b>{whole(v, lang)}</b><br>{pct_text(shares[k], lang)}" for v, k in zip(values, ORDER)],
            textposition="outside",
            textfont={"size": 14},
            cliponaxis=False,
            hovertemplate="%{x}<br>%{y:,}<extra></extra>",
        )
    )
    fig.update_layout(
        **base_layout(
            lang,
            bargap=0.38,
            yaxis={"gridcolor": "rgba(255,255,255,0.08)", "zeroline": False, "range": [0, max(values) * 1.22 if max(values) else 1], "tickfont": {"color": "#b2afd9"}},
            xaxis={"tickfont": {"size": 14}},
        )
    )
    return fig


def sentiment_tile(name, count, share, lang):
    t = TEXT[lang]
    return html.Div(
        [
            html.Div(t["names"][name], className="sent-name"),
            html.Div(countup(pct_text(share, lang), round(share * 100, 1), lang, 1, "%"), className="sent-pct"),
            html.Div(f"{whole(count, lang)} {t['unit']}", className="sent-count"),
            html.Div(html.Div(className="sent-fill", style={"width": f"{share * 100:.1f}%"}), className="sent-bar"),
        ],
        className=f"sent-tile tilt sent-{name.lower()}",
    )


def build_panel(lang, clean, report, mode):
    t = TEXT[lang]
    has_label = bool(report.get("has_label"))
    mode = "true" if (mode == "true" and has_label) else "pred"
    column = "Cam_xuc_that" if mode == "true" else "Cam_xuc_du_doan"
    series = clean[column].dropna()
    counts = series.value_counts().reindex(ORDER, fill_value=0)
    total = int(counts.sum())

    toggle = []
    if has_label:
        toggle = [
            dcc.RadioItems(
                id={"type": "pref", "index": "mode"},
                options=[{"label": t["mode_pred"], "value": "pred"}, {"label": t["mode_true"], "value": "true"}],
                value=mode,
                className="lang-pill mode-pill",
            )
        ]
    head = html.Div(
        [html.Div([html.H2(t["title"], className="panel-title"), html.P(t["sub"], className="panel-sub")]), *toggle],
        className="atlas-head",
    )
    if total == 0:
        return [head, html.Div(t["empty"], className="notice notice-info")]

    shares = counts / total
    top = shares.idxmax()
    total_tile = html.Div(
        [
            html.Div(t["total"], className="sent-name"),
            html.Div(countup(whole(total, lang), total, lang), className="sent-pct total-number"),
            html.Div(t["unit"], className="sent-count"),
            html.Div(html.Div(className="sent-fill", style={"width": "100%"}), className="sent-bar"),
        ],
        className="sent-tile tilt sent-total",
    )
    tiles = html.Div([total_tile] + [sentiment_tile(k, int(counts[k]), float(shares[k]), lang) for k in ORDER], className="sent-grid")

    insight_parts = [
        html.Span("✨", className="insight-icon"),
        html.Span([f"{t['dominant']}: ", html.B(t["names"][top], style={"color": COLORS[top]}), " ", t["dominant_tail"].format(pct=pct_text(float(shares[top]), lang))]),
    ]
    if mode == "pred" and "Do_tin_cay" in clean:
        insight_parts.append(html.Span([f"{t['avg_conf']}: ", html.B(pct_text(float(clean["Do_tin_cay"].mean()), lang))], className="insight-conf"))
    insight = html.Div(insight_parts, className="insight")

    charts = html.Div(
        [
            html.Div([html.Div(t["donut_title"], className="chart-title"), dcc.Graph(figure=donut_figure(counts, total, lang), config={"displayModeBar": False}, style={"height": "380px"})], className="chart-card"),
            html.Div([html.Div(t["bar_title"], className="chart-title"), dcc.Graph(figure=bar_figure(counts, shares, lang), config={"displayModeBar": False}, style={"height": "380px"})], className="chart-card"),
        ],
        className="chart-grid",
    )
    note_text = t["note_pred"].format(acc=pct_text(MODEL_ACCURACY, lang), base=pct_text(BASELINE_ACCURACY, lang)) if mode == "pred" else t["note_true"]
    return [head, tiles, insight, charts, html.P(note_text, className="chart-note")]