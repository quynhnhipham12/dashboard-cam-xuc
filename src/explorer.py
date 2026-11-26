import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from sklearn.feature_extraction.text import CountVectorizer

from src import pipeline
from src.atlas import COLORS, ORDER, TEXT as ATLAS_TEXT, base_layout, countup, pct_text, whole
from src.lab import hex_rgba
from src.ui import icon, icon3d

PAGE_SIZE = 10
SORTS = ["recent", "likes", "conf"]
EXPORT_COLUMNS = ["Ma_bai", "Noi_dung", "Danh_muc", "Ngon_ngu", "Thoi_gian", "Likes", "Comments", "Shares", "Cam_xuc_that", "Cam_xuc_du_doan", "Do_tin_cay"]

TEXT = {
    "vi": {
        "title": "Trung tâm khám phá",
        "sub": "Lọc, tìm kiếm và xem từng bài đăng cùng cảm xúc được dự đoán.",
        "f_search": "Tìm trong nội dung",
        "search_ph": "Gõ từ khóa rồi nhấn Enter…",
        "f_sort": "Sắp xếp",
        "sorts": {"recent": "Mới nhất", "likes": "Nhiều Likes", "conf": "Tin cậy cao"},
        "f_category": "Danh mục bài đăng",
        "f_language": "Ngôn ngữ",
        "f_sentiment": "Nhóm cảm xúc",
        "reset": "Xóa bộ lọc",
        "kpi_match": "Bài đăng phù hợp",
        "kpi_of": "{pct} tổng số bài đăng",
        "kpi_mix": "Cơ cấu cảm xúc",
        "kpi_avg": "Tương tác trung bình mỗi bài",
        "list_title": "Danh sách bài đăng",
        "cols": {"id": "Mã", "content": "Nội dung", "category": "Danh mục", "language": "Ngôn ngữ", "time": "Ngày đăng", "eng": "Tương tác", "pred": "Dự đoán", "true": "Nhãn gốc", "conf": "Tin cậy", "ok": "Khớp"},
        "showing": "Hiển thị {a}–{b} trong {total} bài đăng",
        "page": "Trang {p}/{n}",
        "prev": "← Trước",
        "next": "Sau →",
        "download": "Tải dữ liệu đã lọc (CSV)",
        "trend_title": "Xu hướng số bài đăng theo tháng",
        "trend_none": "Dữ liệu không có cột thời gian hợp lệ để vẽ xu hướng.",
        "kw_title": "Từ khóa đặc trưng theo nhóm cảm xúc",
        "kw_note": "Chỉ số ×N cho biết từ đó xuất hiện nhiều gấp N lần so với mức chung của bộ lọc hiện tại.",
        "kw_none": "Chưa đủ dữ liệu để rút từ khóa.",
        "play_title": "Thử nghiệm AI",
        "play_sub": "Nhập một bài đăng bất kỳ để mô hình dự đoán cảm xúc.",
        "play_ph": "Ví dụ: The new update is amazing, I love it!",
        "play_btn": "Dự đoán cảm xúc",
        "play_result": "Kết quả dự đoán",
        "play_empty": "Hãy nhập nội dung có chữ cái để dự đoán.",
        "play_note": "Mô hình chỉ đạt khoảng 51,7% chính xác trên dữ liệu kiểm thử nên kết quả mang tính tham khảo.",
        "empty": "Không có bài đăng nào khớp bộ lọc hiện tại.",
        "mode_note": "Đang lọc theo",
    },
    "en": {
        "title": "Insight Explorer",
        "sub": "Filter, search and browse every post with its predicted sentiment.",
        "f_search": "Search in content",
        "search_ph": "Type a keyword and press Enter…",
        "f_sort": "Sort by",
        "sorts": {"recent": "Most recent", "likes": "Most Likes", "conf": "High confidence"},
        "f_category": "Post category",
        "f_language": "Language",
        "f_sentiment": "Sentiment group",
        "reset": "Clear filters",
        "kpi_match": "Matching posts",
        "kpi_of": "{pct} of all posts",
        "kpi_mix": "Sentiment mix",
        "kpi_avg": "Average engagement per post",
        "list_title": "Post list",
        "cols": {"id": "ID", "content": "Content", "category": "Category", "language": "Language", "time": "Posted", "eng": "Engagement", "pred": "Predicted", "true": "Original", "conf": "Confidence", "ok": "Match"},
        "showing": "Showing {a}–{b} of {total} posts",
        "page": "Page {p}/{n}",
        "prev": "← Previous",
        "next": "Next →",
        "download": "Download filtered data (CSV)",
        "trend_title": "Monthly posting trend",
        "trend_none": "The data has no valid time column to draw a trend.",
        "kw_title": "Signature keywords by sentiment",
        "kw_note": "The ×N score shows how many times more often a word appears than the overall level of the current filter.",
        "kw_none": "Not enough data to extract keywords.",
        "play_title": "AI Playground",
        "play_sub": "Type any post and let the model predict its sentiment.",
        "play_ph": "Example: The new update is amazing, I love it!",
        "play_btn": "Predict sentiment",
        "play_result": "Prediction result",
        "play_empty": "Please enter content that contains letters.",
        "play_note": "The model reaches only about 51.7% accuracy on test data, so treat the result as a hint.",
        "empty": "No post matches the current filters.",
        "mode_note": "Filtering by",
    },
}


def column_for(mode, has_label):
    return "Cam_xuc_that" if (mode == "true" and has_label) else "Cam_xuc_du_doan"


def filter_frame(clean, ui, has_label=True):
    ui = ui or {}
    column = column_for(ui.get("mode"), has_label)
    frame = clean
    if ui.get("category"):
        frame = frame[frame["Danh_muc"].isin(ui["category"])]
    if ui.get("language"):
        frame = frame[frame["Ngon_ngu"].isin(ui["language"])]
    if ui.get("sentiment"):
        frame = frame[frame[column].isin(ui["sentiment"])]
    query = (ui.get("query") or "").strip().lower()
    if query:
        frame = frame[frame["Noi_dung"].str.lower().str.contains(query, regex=False)]
    return frame


def export_frame(frame):
    export = frame[EXPORT_COLUMNS].copy()
    export["Thoi_gian"] = export["Thoi_gian"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return export


def predict_text(text):
    cleaned = pipeline.normalize_text(text or "")
    if not cleaned:
        return None
    model = pipeline.get_model()
    probs = model.predict_proba([cleaned])[0]
    classes = list(model.classes_)
    return {"text": text, "label": classes[int(np.argmax(probs))], "probs": {c: float(p) for c, p in zip(classes, probs)}}


def keywords(frame, column, top_n=8):
    if len(frame) < 30:
        return None
    try:
        matrix = CountVectorizer(min_df=3, max_df=0.6, binary=True).fit(frame["Noi_dung_sach"])
        vec = matrix
        data = vec.transform(frame["Noi_dung_sach"])
    except ValueError:
        return None
    vocab = np.array(vec.get_feature_names_out())
    overall = np.asarray(data.mean(axis=0)).ravel()
    result = {}
    for key in ORDER:
        mask = (frame[column] == key).to_numpy()
        if mask.sum() < 10:
            result[key] = []
            continue
        counts = np.asarray(data[mask].sum(axis=0)).ravel()
        rate = counts / mask.sum()
        lift = np.divide(rate, overall, out=np.zeros_like(rate), where=overall > 0)
        eligible = np.where(counts >= 5)[0]
        order = eligible[np.argsort(-lift[eligible])][:top_n]
        result[key] = [(vocab[i], float(lift[i]), int(counts[i])) for i in order]
    return result


def trend_figure(frame, column, lang):
    data = frame.dropna(subset=["Thoi_gian"])
    if data.empty:
        return None
    monthly = data.groupby([pd.Grouper(key="Thoi_gian", freq="MS"), column]).size().unstack(fill_value=0).reindex(columns=ORDER, fill_value=0)
    fig = go.Figure()
    for key in ORDER:
        fig.add_trace(
            go.Scatter(
                x=monthly.index,
                y=monthly[key],
                name=key,
                mode="lines",
                stackgroup="one",
                line={"width": 1.8, "color": COLORS[key], "shape": "spline", "smoothing": 0.7},
                fillcolor=hex_rgba(COLORS[key], 0.5),
                hovertemplate="%{x|%m/%Y}<br>%{y:,}<extra>" + key + "</extra>",
            )
        )
    fig.update_layout(
        **base_layout(
            lang,
            margin={"l": 40, "r": 20, "t": 20, "b": 30},
            legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 12}},
            xaxis={"gridcolor": "rgba(255,255,255,0.06)", "tickfont": {"color": "#b2afd9"}},
            yaxis={"gridcolor": "rgba(255,255,255,0.08)", "zeroline": False, "tickfont": {"color": "#b2afd9"}},
            hovermode="x unified",
        )
    )
    return fig


def chip_checklist(index, options, value, extra=""):
    return dcc.Checklist(id={"type": "pref", "index": index}, options=options, value=value or [], className=f"chip-check {extra}".strip())


def badge(label):
    if not label or (isinstance(label, float) and pd.isna(label)):
        return html.Span("–", className="badge badge-none")
    return html.Span(label, className=f"badge badge-{str(label).lower()}")


def confidence_cell(value):
    return html.Td([html.Div(html.Div(style={"width": f"{value * 100:.0f}%"}, className="conf-fill"), className="conf-bar"), html.Span(f"{value * 100:.0f}%", className="conf-text")], className="conf-cell")


def post_row(row, show_true):
    stamp = row["Thoi_gian"]
    cells = [
        html.Td(str(row["Ma_bai"]), className="cell-id"),
        html.Td(row["Noi_dung"], className="post-text", title=row["Noi_dung"]),
        html.Td([html.Div(row["Danh_muc"]), html.Div(row["Ngon_ngu"], className="sub-cell")]),
        html.Td("–" if pd.isna(stamp) else f"{stamp:%Y-%m-%d}", className="nowrap"),
        html.Td([html.Span([icon("thumb"), f"{int(row['Likes']):,}"], className="eng-item"), html.Span([icon("message"), f"{int(row['Comments']):,}"], className="eng-item"), html.Span([icon("share"), f"{int(row['Shares']):,}"], className="eng-item")], className="nowrap eng-cell"),
        html.Td(badge(row["Cam_xuc_du_doan"])),
    ]
    if show_true:
        cells.append(html.Td(badge(row["Cam_xuc_that"])))
    cells.append(confidence_cell(float(row["Do_tin_cay"])))
    if show_true:
        known = pd.notna(row["Cam_xuc_that"])
        ok = known and row["Cam_xuc_that"] == row["Cam_xuc_du_doan"]
        cells.append(html.Td("✓" if ok else ("✗" if known else "–"), className="ok-yes" if ok else ("ok-no" if known else "ok-none")))
    return html.Tr(cells)


def playground_card(t, ui, lang):
    result = (ui or {}).get("playground")
    blocks = [
        html.Div([icon3d("cpu", "violet", "icon3d-md"), html.Div([html.H3(t["play_title"], className="source-title"), html.P(t["play_sub"], className="source-hint")])], className="play-head"),
        dcc.Textarea(id={"type": "field", "index": "playground"}, value=(result or {}).get("text", "") if isinstance(result, dict) else "", placeholder=t["play_ph"], className="play-input"),
        html.Button(t["play_btn"], id={"type": "act-btn", "index": "predict"}, className="btn btn-primary btn-sm", n_clicks=0),
    ]
    if result == "empty":
        blocks.append(html.Div(t["play_empty"], className="notice notice-info"))
    elif result:
        bars = []
        for key in ORDER:
            probability = result["probs"].get(key, 0.0)
            bars.append(
                html.Div(
                    [
                        html.Span(key, className="prob-name"),
                        html.Div(html.Div(style={"width": f"{probability * 100:.1f}%", "background": COLORS[key]}, className="prob-fill"), className="prob-bar"),
                        html.Span(pct_text(probability, lang), className="prob-value"),
                    ],
                    className="prob-row",
                )
            )
        blocks.append(
            html.Div(
                [html.Div([html.Span(t["play_result"], className="mini-head-inline"), badge(result["label"])], className="play-verdict"), *bars, html.P(t["play_note"], className="chart-note")],
                className="play-result",
            )
        )
    return html.Div(blocks, className="chart-card play-card")


def build_panel(lang, clean, report, ui):
    t = TEXT[lang]
    atlas_t = ATLAS_TEXT[lang]
    ui = ui or {}
    has_label = bool(report.get("has_label"))
    mode = "true" if (ui.get("mode") == "true" and has_label) else "pred"
    column = column_for(mode, has_label)
    sort = ui.get("sort", "recent") if ui.get("sort", "recent") in SORTS else "recent"

    categories = clean["Danh_muc"].value_counts()
    languages = clean["Ngon_ngu"].value_counts()
    frame = filter_frame(clean, ui, has_label)
    total_all = len(clean)
    matched = len(frame)

    toggle = []
    if has_label:
        toggle = [dcc.RadioItems(id={"type": "pref", "index": "mode"}, options=[{"label": atlas_t["mode_pred"], "value": "pred"}, {"label": atlas_t["mode_true"], "value": "true"}], value=mode, className="lang-pill mode-pill")]
    head = html.Div([html.Div([html.H2(t["title"], className="panel-title"), html.P(t["sub"], className="panel-sub")]), html.Div(toggle, className="control-row")], className="atlas-head")

    filters = html.Div(
        [
            html.Div(
                [
                    html.Div([html.Label(t["f_search"], className="filter-label"), dcc.Input(id={"type": "pref", "index": "query"}, type="text", value=ui.get("query", ""), debounce=True, placeholder=t["search_ph"], className="search-input")], className="filter-field grow"),
                    html.Div([html.Label(t["f_sort"], className="filter-label"), dcc.RadioItems(id={"type": "pref", "index": "sort"}, options=[{"label": t["sorts"][s], "value": s} for s in SORTS], value=sort, className="lang-pill mode-pill")], className="filter-field"),
                    html.Button(t["reset"], id={"type": "act-btn", "index": "reset"}, className="btn btn-ghost btn-sm reset-btn", n_clicks=0),
                ],
                className="filter-row",
            ),
            html.Div([html.Label(t["f_category"], className="filter-label"), chip_checklist("category", [{"label": f"{name} · {whole(n, lang)}", "value": name} for name, n in categories.items()], ui.get("category"))], className="filter-field"),
            html.Div(
                [
                    html.Div([html.Label(t["f_sentiment"], className="filter-label"), chip_checklist("sentiment", [{"label": k, "value": k} for k in ORDER], ui.get("sentiment"), "sent-check")], className="filter-field"),
                    html.Div([html.Label(t["f_language"], className="filter-label"), chip_checklist("language", [{"label": f"{name} · {whole(n, lang)}", "value": name} for name, n in languages.items()], ui.get("language"))], className="filter-field grow"),
                ],
                className="filter-row",
            ),
        ],
        className="filter-bar",
    )
    blocks = [head, filters]

    if matched == 0:
        blocks.append(html.Div([icon("search"), html.Span(t["empty"])], className="notice notice-info"))
        blocks.append(playground_card(t, ui, lang))
        return blocks

    counts = frame[column].value_counts().reindex(ORDER, fill_value=0)
    labelled = int(counts.sum())
    shares = counts / labelled if labelled else counts * 0
    segments = [html.Div(className=f"mix-seg mix-{k.lower()}", style={"width": f"{shares[k] * 100:.1f}%"}, title=f"{k}: {pct_text(float(shares[k]), lang)}") for k in ORDER]
    legend = [html.Span([html.Span(className=f"dot dot-{k.lower()}"), f"{k} {pct_text(float(shares[k]), lang)}"], className="mix-legend-item") for k in ORDER]
    averages = frame[["Likes", "Comments", "Shares"]].mean()
    kpis = html.Div(
        [
            html.Div([html.Div(t["kpi_match"], className="sent-name"), html.Div(countup(whole(matched, lang), matched, lang), className="sent-pct"), html.Div(t["kpi_of"].format(pct=pct_text(matched / total_all, lang)), className="sent-count")], className="sent-tile tilt sent-total"),
            html.Div([html.Div(t["kpi_mix"], className="sent-name"), html.Div(segments, className="mix-bar"), html.Div(legend, className="mix-legend")], className="sent-tile tilt mix-tile"),
            html.Div(
                [
                    html.Div(t["kpi_avg"], className="sent-name"),
                    html.Div([html.Div([icon("thumb"), html.B(f"{averages['Likes']:.1f}".replace(".", "," if lang == "vi" else "."))], className="avg-item"), html.Div([icon("message"), html.B(f"{averages['Comments']:.1f}".replace(".", "," if lang == "vi" else "."))], className="avg-item"), html.Div([icon("share"), html.B(f"{averages['Shares']:.1f}".replace(".", "," if lang == "vi" else "."))], className="avg-item")], className="avg-row"),
                ],
                className="sent-tile tilt sent-neutral avg-tile",
            ),
        ],
        className="explorer-kpis",
    )
    blocks.append(kpis)

    ordered = frame.sort_values("Thoi_gian", ascending=False, na_position="last") if sort == "recent" else frame.sort_values("Likes" if sort == "likes" else "Do_tin_cay", ascending=False)
    pages = max(1, -(-matched // PAGE_SIZE))
    page = min(max(int(ui.get("page", 0) or 0), 0), pages - 1)
    window = ordered.iloc[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    cols = t["cols"]
    header_cells = [cols["id"], cols["content"], f"{cols['category']} / {cols['language']}", cols["time"], cols["eng"], cols["pred"]] + ([cols["true"]] if has_label else []) + [cols["conf"]] + ([cols["ok"]] if has_label else [])
    table = html.Div(html.Table([html.Thead(html.Tr([html.Th(c) for c in header_cells])), html.Tbody([post_row(row, has_label) for _, row in window.iterrows()])], className="data-table post-table"), className="table-wrap")
    pager = html.Div(
        [
            html.Div(t["showing"].format(a=page * PAGE_SIZE + 1, b=min((page + 1) * PAGE_SIZE, matched), total=whole(matched, lang)), className="pager-info"),
            html.Div(
                [
                    html.Button(t["prev"], id={"type": "act-btn", "index": "page-prev"}, className="btn btn-ghost btn-sm", disabled=page <= 0, n_clicks=0),
                    html.Span(t["page"].format(p=page + 1, n=pages), className="pager-page"),
                    html.Button(t["next"], id={"type": "act-btn", "index": "page-next"}, className="btn btn-ghost btn-sm", disabled=page >= pages - 1, n_clicks=0),
                ],
                className="pager-buttons",
            ),
            html.Button(t["download"], id={"type": "act-btn", "index": "download"}, className="btn btn-primary btn-sm", n_clicks=0),
        ],
        className="pager",
    )
    blocks.append(html.Div([html.Div(t["list_title"], className="chart-title"), table, pager], className="chart-card"))

    fig = trend_figure(frame, column, lang)
    trend_body = dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "320px"}) if fig is not None else html.P(t["trend_none"], className="chart-note")
    blocks.append(html.Div([html.Div(t["trend_title"], className="chart-title"), trend_body], className="chart-card"))

    words = keywords(frame, column)
    if words is None or not any(words.values()):
        kw_body = html.P(t["kw_none"], className="chart-note")
    else:
        kw_body = html.Div(
            [
                html.Div([html.Div([html.Span(className=f"dot dot-{k.lower()}"), html.Span(k, style={"color": COLORS[k]})], className="kw-head"), html.Div([html.Span([w, html.Small(f" ×{lift:.1f}".replace(".", "," if lang == "vi" else "."))], className=f"kw-chip kw-{k.lower()}", title=f"{count}") for w, lift, count in words[k]], className="kw-list")], className="kw-col")
                for k in ORDER
            ],
            className="kw-grid",
        )
    blocks.append(html.Div([html.Div(t["kw_title"], className="chart-title"), kw_body, html.P(t["kw_note"], className="chart-note")], className="chart-card"))
    blocks.append(playground_card(t, ui, lang))
    return blocks