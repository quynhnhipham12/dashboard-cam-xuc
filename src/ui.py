from urllib.parse import quote

from dash import html

ICONS = {
    "upload": '<path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.2"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "filter": '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "pie": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "text": '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>',
    "tag": '<path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "thumb": '<path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>',
    "message": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
    "smile": '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "sliders": '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
    "eye": '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
}

ICON_CSS_HEAD = ".ico{display:inline-block;width:1em;height:1em;flex:none;background-color:currentColor;-webkit-mask:var(--ico) center/contain no-repeat;mask:var(--ico) center/contain no-repeat}"


def _uri(inner):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    return 'url("data:image/svg+xml,' + quote(svg, safe="") + '")'


def icon_css():
    return ICON_CSS_HEAD + "".join(f".ico-{name}{{--ico:{_uri(inner)}}}" for name, inner in ICONS.items())


def icon(name, extra=""):
    return html.Span(className=f"ico ico-{name} {extra}".strip())


def icon3d(name, tone="violet", extra=""):
    return html.Div([html.Span(className="i3-base"), html.Span(className=f"ico ico-{name} i3-glyph")], className=f"icon3d tone-{tone} {extra}".strip())


SPLASH_CSS = """
@property --r{syntax:"<percentage>";inherits:false;initial-value:0%}
#vl-splash{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;overflow:hidden;font-family:"Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",sans-serif;
background:radial-gradient(900px 620px at 50% 38%,#31369a 0%,#181d5c 52%,#0b1030 100%);
-webkit-mask-image:radial-gradient(circle at 50% 50%,transparent var(--r),#000 calc(var(--r) + 1.5px));mask-image:radial-gradient(circle at 50% 50%,transparent var(--r),#000 calc(var(--r) + 1.5px));
animation:vls-failsafe .01s 8s forwards}
#vl-splash.vl-out{animation:vls-iris 1.05s cubic-bezier(.7,0,.2,1) forwards}
@keyframes vls-iris{to{--r:165%}}
@keyframes vls-failsafe{to{opacity:0;visibility:hidden}}
.vls-grid{position:absolute;inset:0;opacity:.35;background-image:linear-gradient(rgba(139,108,255,.25) 1px,transparent 1px),linear-gradient(90deg,rgba(139,108,255,.25) 1px,transparent 1px);background-size:56px 56px;-webkit-mask-image:radial-gradient(circle at 50% 50%,#000,transparent 68%);mask-image:radial-gradient(circle at 50% 50%,#000,transparent 68%);animation:vls-grid 6s linear infinite}
@keyframes vls-grid{to{background-position:56px 56px}}
.vls-core{position:relative;display:grid;place-items:center;gap:26px;text-align:center}
.vls-glow{position:absolute;width:min(620px,92vw);height:min(620px,92vw);border-radius:50%;background:radial-gradient(closest-side,rgba(139,108,255,.55),rgba(255,111,177,.2) 55%,transparent 72%);filter:blur(10px);animation:vls-pulse 3s ease-in-out infinite}
@keyframes vls-pulse{50%{transform:scale(1.12);opacity:.85}}
.vls-ring{position:absolute;border-radius:50%;border:1px solid rgba(167,139,250,.45)}
.vls-ring-a{width:min(520px,84vw);height:min(520px,84vw);border-style:dashed;animation:vls-spin 18s linear infinite}
.vls-ring-b{width:min(400px,70vw);height:min(400px,70vw);border-color:rgba(79,216,255,.4);animation:vls-spin 12s linear infinite reverse}
@keyframes vls-spin{to{transform:rotate(360deg)}}
.vls-mark{position:relative;width:min(380px,66vw);filter:drop-shadow(0 18px 46px rgba(139,108,255,.7)) drop-shadow(0 0 22px rgba(167,139,250,.6));animation:vls-mark 1.5s cubic-bezier(.2,.8,.2,1) both,vls-float 5s 1.5s ease-in-out infinite}
@keyframes vls-mark{from{opacity:0;transform:scale(.5) rotate(-10deg);filter:blur(18px)}to{opacity:1;transform:none}}
@keyframes vls-float{50%{transform:translateY(-10px)}}
.vls-word{position:relative;font-weight:800;font-size:clamp(26px,4vw,36px);letter-spacing:.28em;padding-left:.28em;background:linear-gradient(90deg,#fff,#c9b8ff,#8fe9ff,#fff);background-size:250% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:vls-word 1.6s .5s cubic-bezier(.2,.8,.2,1) both,vls-shimmer 3s 2s linear infinite}
@keyframes vls-word{from{opacity:0;letter-spacing:.7em;filter:blur(8px)}to{opacity:1;letter-spacing:.28em;filter:none}}
@keyframes vls-shimmer{to{background-position:-250% 0}}
.vls-bar{position:relative;width:min(260px,60vw);height:3px;border-radius:99px;background:rgba(255,255,255,.14);overflow:hidden}
.vls-bar span{display:block;height:100%;width:0;border-radius:inherit;background:linear-gradient(90deg,#8b6cff,#ff6fb1,#4fd8ff);box-shadow:0 0 14px rgba(139,108,255,.9);animation:vls-bar 2.1s cubic-bezier(.4,0,.2,1) forwards}
@keyframes vls-bar{to{width:100%}}
#vl-splash.vl-out .vls-core{animation:vls-core-out .9s cubic-bezier(.7,0,.2,1) forwards}
@keyframes vls-core-out{to{transform:scale(1.35);opacity:0;filter:blur(6px)}}
"""

SPLASH_HTML = """<div id="vl-splash"><div class="vls-grid"></div><div class="vls-core"><div class="vls-glow"></div><div class="vls-ring vls-ring-a"></div><div class="vls-ring vls-ring-b"></div><img class="vls-mark" src="/assets/brand/logo-mark.png" alt=""><div class="vls-word">VibeLens</div><div class="vls-bar"><span></span></div></div></div>
<script>(function(){var d=document.documentElement,t0=performance.now(),done=false;d.classList.add("vl-intro");
function finish(){if(done)return;done=true;var s=document.getElementById("vl-splash");d.classList.add("vl-ready");if(!s){d.classList.remove("vl-intro");return;}s.classList.add("vl-out");setTimeout(function(){if(s.parentNode)s.parentNode.removeChild(s);d.classList.remove("vl-intro");},1300);}
function go(){setTimeout(finish,Math.max(0,2400-(performance.now()-t0)));}
if(document.readyState==="complete")go();else window.addEventListener("load",go);
setTimeout(finish,6500);})();</script>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<style>__ICON_CSS____SPLASH_CSS__</style>
</head>
<body>
__SPLASH__
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>"""


def index_string():
    return INDEX_TEMPLATE.replace("__ICON_CSS__", icon_css()).replace("__SPLASH_CSS__", SPLASH_CSS).replace("__SPLASH__", SPLASH_HTML)