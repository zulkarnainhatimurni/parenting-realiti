#!/usr/bin/env python3
"""Bina laman statik Parenting Realiti daripada src/artikel.md.

Domain ditetapkan dalam src/artikel.json (site_url).
"""
import html
import json
import math
import re
import shutil
from pathlib import Path

import markdown

SITE_NAME = "Parenting Realiti"
AUTHOR = "Zulkarnain Ramlan"
THREADS_URL = "https://www.threads.com/@zullkarrnain"
TAGLINE = "Berita hari ini, apa maksudnya untuk anak kita."

ROOT = Path(__file__).parent
SITE_URL = json.loads((ROOT / "src" / "artikel.json").read_text(encoding="utf-8"))["site_url"].rstrip("/")
SRC = ROOT / "src" / "artikel.md"
OUT = ROOT / "site"

BULAN = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
         "Ogos", "September", "Oktober", "November", "Disember"]

# Metadata artikel (slug, tarikh, topik) disimpan dalam src/artikel.json,
# ikut urutan yang sama dengan "## Artikel N:" dalam src/artikel.md.
CONFIG = json.loads((Path(__file__).parent / "src" / "artikel.json").read_text(encoding="utf-8"))
META = CONFIG["articles"]
TOPICS = ["Keselamatan", "Pendidikan", "Kecemasan", "Makanan & kesihatan"]


def tarikh(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {BULAN[int(m) - 1]} {y}"


def esc(s):
    return html.escape(s, quote=True)


def strip_md(s):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"[*_`>#]", "", s).strip()


def parse_articles(text):
    parts = re.split(r"^## Artikel \d+: ", text, flags=re.M)[1:]
    arts = []
    for part, meta in zip(parts, META):
        lines = part.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        desc = re.search(r"\*\*Meta description:\*\*\s*(.+)", body).group(1).strip()
        kw = re.search(r"\*\*Keyword sekunder:\*\*\s*(.+)", body).group(1).strip()
        body = re.sub(r"\*\*Meta description:\*\*.+\n?", "", body)
        body = re.sub(r"\*\*Keyword sekunder:\*\*.+\n?", "", body)
        body = body.strip()
        # Asingkan baris Sumber
        sources = []
        m = re.search(r"^Sumber:\s*(.+)$", body, flags=re.M)
        if m:
            sources = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", m.group(1))
            body = body[: m.start()].rstrip() + body[m.end():]
        # Asingkan FAQ
        faq = []
        fm = re.search(r"^### Soalan lazim\s*\n(.*?)(?=^### |\Z)", body, flags=re.M | re.S)
        if fm:
            for q, a in re.findall(r"\*\*(.+?)\*\*\s*(.+)", fm.group(1)):
                faq.append((q.strip(), a.strip()))
            body = body[: fm.start()] + body[fm.end():]
        words = len(re.findall(r"\w+", strip_md(body)))
        first_para = next(p for p in body.split("\n\n") if p and not p.startswith("#"))
        arts.append(dict(meta, title=title, desc=desc, keywords=kw, body=body, faq=faq,
                         sources=sources, minutes=max(1, math.ceil(words / 200)),
                         excerpt=strip_md(first_para)))
    return arts


CHECK_RE = re.compile(r"^- \[ \] (.+)$", re.M)


def render_body(md_text, slug):
    # Tukar checklist kepada senarai kotak semak sebenar
    counter = {"n": 0}

    def chk(m):
        counter["n"] += 1
        return f"- @@CHK{counter['n']}@@{m.group(1)}"

    md_text = CHECK_RE.sub(chk, md_text)
    out = markdown.markdown(md_text, extensions=["tables", "sane_lists"])

    def box(m):
        i = m.group(1)
        return (f'<label class="check"><input type="checkbox" data-key="{slug}-{i}">'
                f'<span>')
    out = re.sub(r"@@CHK(\d+)@@", box, out)
    out = re.sub(r'(<label class="check">.*?)</li>', r"\1</span></label></li>", out)
    out = out.replace("<ul>\n<li><label", '<ul class="checklist">\n<li><label')
    # Pautan luar buka tab baru
    out = re.sub(r'<a href="(https?://[^"]+)">',
                 r'<a href="\1" target="_blank" rel="noopener">', out)
    # Bungkus jadual supaya boleh skrol di telefon
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # Beri id pada subtajuk
    def hid(m):
        text = re.sub(r"<[^>]+>", "", m.group(1))
        anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return f'<h2 id="{anchor}">{m.group(1)}</h2>'
    out = re.sub(r"<h3>(.*?)</h3>", hid, out)
    return out


def head(title, desc, path, extra=""):
    url = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
    tag = CONFIG.get("google_tag", "")
    gtag = (f'<script async src="https://www.googletagmanager.com/gtm.js?id={tag}"></script>\n'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());</script>\n") if tag else ""
    verify = CONFIG.get("google_site_verification", "")
    if verify and not path:
        gtag += f'<meta name="google-site-verification" content="{verify}" />\n'
    return f"""<!DOCTYPE html>
<html lang="ms">
<head>
{gtag}<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{AUTHOR}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="ms_MY">
<meta name="twitter:card" content="summary">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#2445A6">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232445A6'/%3E%3Crect x='7' y='21' width='18' height='4' rx='1' fill='%23F4C430'/%3E%3Cpath d='M10 18V8h6.2a4.4 4.4 0 0 1 0 8.8H10' fill='none' stroke='white' stroke-width='2.6'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@500;700;800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{'../' if path.startswith('artikel/') else ''}style.css">
{extra}
</head>
"""


def header(prefix, current=""):
    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{prefix}{href}"{cur}>{label}</a>'
    return f"""<a class="skip" href="#utama">Langkau ke kandungan</a>
<header class="site-header">
  <div class="wrap header-row">
    <a class="wordmark" href="{prefix}index.html" aria-label="{SITE_NAME}, halaman utama">
      <span class="wm-a">Parenting</span><span class="wm-b">Realiti</span>
    </a>
    <nav class="main-nav" aria-label="Utama">
      {nav('index.html#artikel', 'Artikel', 'artikel')}
      {nav('tentang.html', 'Tentang', 'tentang')}
      <a href="{THREADS_URL}" target="_blank" rel="noopener">Threads</a>
    </nav>
  </div>
</header>
"""


def footer(prefix):
    return f"""<footer class="site-footer">
  <div class="wrap footer-row">
    <div>
      <p class="footer-mark">Parenting Realiti</p>
      <p class="footer-note">Ditulis oleh {AUTHOR}. Isu semasa, dibaca dari sudut seorang bapa.</p>
    </div>
    <nav class="footer-nav" aria-label="Kaki laman">
      <a href="{prefix}index.html#artikel">Semua artikel</a>
      <a href="{prefix}tentang.html">Tentang penulis</a>
      <a href="{THREADS_URL}" target="_blank" rel="noopener">Ikuti di Threads</a>
    </nav>
  </div>
  <div class="wrap footer-legal">
    <p>&copy; 2026 {AUTHOR}. Maklumat dalam blog ini untuk panduan umum, bukan nasihat perubatan atau perundangan. Rujuk pihak berkuasa atau doktor untuk keadaan anda.</p>
  </div>
</footer>
"""


SCRIPT = """<script>
(function(){
  var bar=document.querySelector('.progress span');
  if(bar){
    var art=document.querySelector('.article-body');
    var tick=function(){
      var r=art.getBoundingClientRect();
      var total=art.offsetHeight-window.innerHeight;
      var p=total>0?Math.min(1,Math.max(0,-r.top/total)):1;
      bar.style.transform='scaleX('+p+')';
    };
    document.addEventListener('scroll',tick,{passive:true});tick();
  }
  document.querySelectorAll('.check input').forEach(function(cb){
    var k='pr-'+cb.dataset.key;
    try{cb.checked=localStorage.getItem(k)==='1';}catch(e){}
    cb.addEventListener('change',function(){try{localStorage.setItem(k,cb.checked?'1':'0');}catch(e){}});
  });
  var copy=document.querySelector('[data-copy]');
  if(copy){copy.addEventListener('click',function(){
    var done=function(){copy.textContent='Pautan disalin';setTimeout(function(){copy.textContent='Salin pautan';},2000);};
    try{navigator.clipboard.writeText(location.href).then(done,done);}catch(e){done();}
  });}
  var chips=document.querySelectorAll('[data-filter]');
  chips.forEach(function(c){c.addEventListener('click',function(){
    var t=c.dataset.filter;
    chips.forEach(function(x){x.setAttribute('aria-pressed',x===c?'true':'false');});
    document.querySelectorAll('.entry').forEach(function(e){
      e.hidden=!(t==='semua'||e.dataset.topic===t);
    });
  });});
})();
</script>"""


def topic_key(t):
    return re.sub(r"[^a-z]+", "-", t.lower()).strip("-")


def build_article(a, arts):
    i = arts.index(a)
    path = f"artikel/{a['slug']}.html"
    url = f"{SITE_URL}/{path}"
    ld = [{
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a["title"], "description": a["desc"],
        "datePublished": a["date"], "dateModified": a["date"], "inLanguage": "ms-MY",
        "keywords": a["keywords"], "mainEntityOfPage": url,
        "author": {"@type": "Person", "name": AUTHOR, "url": f"{SITE_URL}/tentang.html"},
        "publisher": {"@type": "Person", "name": AUTHOR},
    }]
    if a["faq"]:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": [{"@type": "Question", "name": q,
                                   "acceptedAnswer": {"@type": "Answer", "text": strip_md(ans)}}
                                  for q, ans in a["faq"]]})
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    extra = (f'<meta property="og:type" content="article">\n'
             f'<meta property="article:published_time" content="{a["date"]}">\n'
             f'<meta name="keywords" content="{esc(a["keywords"])}">\n{ld_html}')

    faq_html = ""
    if a["faq"]:
        items = "".join(
            f'<details><summary>{esc(q)}</summary><div>{markdown.markdown(ans)}</div></details>'
            for q, ans in a["faq"])
        faq_html = f'<section class="faq" aria-labelledby="faq-h"><h2 id="faq-h">Soalan lazim</h2>{items}</section>'

    src_html = ""
    if a["sources"]:
        lis = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}</a></li>'
                      for n, u in a["sources"])
        src_html = f'<section class="sources" aria-labelledby="src-h"><h2 id="src-h">Sumber berita</h2><ul>{lis}</ul></section>'

    share_text = esc(f"{a['title']} {url}")
    related = [x for x in arts if x is not a and x["topic"] == a["topic"]][:2]
    if len(related) < 2:
        related += [x for x in arts if x is not a and x not in related][: 2 - len(related)]
    rel_html = "".join(
        f'<a class="rel" href="{x["slug"]}.html"><span class="rel-topic">{x["topic"]}</span>'
        f'<span class="rel-title">{esc(x["title"])}</span></a>' for x in related)

    nav_prev = arts[i + 1] if i + 1 < len(arts) else None

    page = head(f"{a['title']} | {SITE_NAME}", a["desc"], path, extra)
    page += f"""<body class="page-article">
{header('../')}
<div class="progress" aria-hidden="true"><span></span></div>
<main id="utama">
  <article>
    <header class="article-head wrap-narrow">
      <p class="crumb"><a href="../index.html#artikel">Artikel</a><span aria-hidden="true">/</span><span class="tag tag-{topic_key(a['topic'])}">{a['topic']}</span></p>
      <h1>{esc(a['title'])}</h1>
      <p class="standfirst">{esc(a['desc'])}</p>
      <div class="byline">
        <span class="avatar" aria-hidden="true">ZR</span>
        <div><a href="../tentang.html" class="byline-name">{AUTHOR}</a>
        <span class="byline-meta"><time datetime="{a['date']}">{tarikh(a['date'])}</time>, {a['minutes']} minit bacaan</span></div>
      </div>
    </header>
    <div class="article-body wrap-narrow">
      {render_body(a['body'], a['slug'])}
      {faq_html}
      {src_html}
      <aside class="share" aria-label="Kongsi artikel">
        <p>Rasa berguna? Kongsikan dengan keluarga.</p>
        <div class="share-row">
          <a class="btn" href="https://wa.me/?text={share_text}" target="_blank" rel="noopener">WhatsApp</a>
          <a class="btn" href="https://www.threads.com/intent/post?text={share_text}" target="_blank" rel="noopener">Threads</a>
          <a class="btn" href="https://www.facebook.com/sharer/sharer.php?u={esc(url)}" target="_blank" rel="noopener">Facebook</a>
          <button class="btn" type="button" data-copy>Salin pautan</button>
        </div>
      </aside>
    </div>
  </article>
  <section class="related wrap" aria-labelledby="rel-h">
    <h2 id="rel-h">Baca seterusnya</h2>
    <div class="rel-grid">{rel_html}</div>
  </section>
</main>
{footer('../')}
{SCRIPT}
</body>
</html>"""
    (OUT / path).write_text(page, encoding="utf-8")


def build_index(arts):
    ordered = list(reversed(arts))  # terbaru dahulu
    lead = ordered[0]
    chips = '<button type="button" data-filter="semua" aria-pressed="true">Semua</button>' + "".join(
        f'<button type="button" data-filter="{topic_key(t)}" aria-pressed="false">{t}</button>' for t in TOPICS)
    entries = "".join(f"""
      <li class="entry" data-topic="{topic_key(a['topic'])}">
        <a href="artikel/{a['slug']}.html">
          <span class="entry-meta"><span class="tag tag-{topic_key(a['topic'])}">{a['topic']}</span><time datetime="{a['date']}">{tarikh(a['date'])}</time></span>
          <span class="entry-title">{esc(a['title'])}</span>
          <span class="entry-excerpt">{esc(a['desc'])}</span>
          <span class="entry-time">{a['minutes']} minit bacaan</span>
        </a>
      </li>""" for a in ordered)
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": SITE_NAME, "url": f"{SITE_URL}/",
          "inLanguage": "ms-MY", "author": {"@type": "Person", "name": AUTHOR}}
    desc = ("Blog parenting oleh Zulkarnain Ramlan. Isu semasa Malaysia diterjemah kepada langkah "
            "praktikal untuk ibu bapa: keselamatan, pendidikan dan persediaan kecemasan.")
    page = head(f"{SITE_NAME}: blog parenting isu semasa Malaysia oleh {AUTHOR}", desc, "",
                f'<meta property="og:type" content="website">\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    page += f"""<body class="page-home">
{header('', 'artikel')}
<main id="utama">
  <section class="hero wrap">
    <div class="hero-text">
      <h1>{TAGLINE}</h1>
      <p class="hero-sub">Saya {AUTHOR}, seorang bapa yang setiap hari bersama kanak-kanak. Di sini saya baca berita semasa Malaysia dan pecahkannya kepada langkah yang ibu bapa boleh buat di rumah, malam ini juga.</p>
      <p class="hero-actions"><a class="btn btn-solid" href="#artikel">Baca artikel terkini</a><a class="btn" href="{THREADS_URL}" target="_blank" rel="noopener">Ikuti di Threads</a></p>
    </div>
    <a class="lead" href="artikel/{lead['slug']}.html">
      <span class="lead-label">Terbaru</span>
      <span class="lead-meta"><span class="tag tag-{topic_key(lead['topic'])}">{lead['topic']}</span><time datetime="{lead['date']}">{tarikh(lead['date'])}</time></span>
      <span class="lead-title">{esc(lead['title'])}</span>
      <span class="lead-excerpt">{esc(lead['excerpt'])}</span>
      <span class="lead-more">Baca artikel, {lead['minutes']} minit</span>
    </a>
  </section>

  <section class="wrap" aria-labelledby="how-h"><div class="how">
    <h2 id="how-h" class="visually-hidden">Cara blog ini ditulis</h2>
    <div class="how-item"><p class="how-k">Bermula dengan berita</p><p>Setiap artikel bermula daripada isu yang disahkan oleh portal berita utama Malaysia, dengan pautan sumber di hujung.</p></div>
    <div class="how-item"><p class="how-k">Dibaca sebagai ibu bapa</p><p>Soalannya sentiasa sama: apa maksud berita ini untuk anak kecil di rumah kita?</p></div>
    <div class="how-item"><p class="how-k">Berakhir dengan tindakan</p><p>Senarai semak, langkah dan soalan lazim yang boleh terus digunakan, bukan sekadar pendapat.</p></div>
  </div></section>

  <section id="artikel" class="archive wrap" aria-labelledby="arc-h">
    <div class="archive-head">
      <h2 id="arc-h">Semua artikel</h2>
      <div class="chips" role="group" aria-label="Tapis ikut topik">{chips}</div>
    </div>
    <ol class="entries" reversed>{entries}
    </ol>
  </section>

  <section class="wrap" aria-labelledby="au-h"><div class="author">
    <span class="avatar avatar-lg" aria-hidden="true">ZR</span>
    <div>
      <h2 id="au-h">Tentang penulis</h2>
      <p>{AUTHOR} ialah seorang bapa yang bekerja dalam bidang pendidikan kanak-kanak. Dia menulis Parenting Realiti untuk ibu bapa yang sibuk tetapi mahu faham isu semasa dengan cepat, dan tahu apa yang perlu dibuat seterusnya.</p>
      <p><a href="tentang.html">Kenali penulis</a></p>
    </div>
  </div></section>
</main>
{footer('')}
{SCRIPT}
</body>
</html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")


def build_about(arts):
    desc = f"Tentang {AUTHOR}, penulis blog Parenting Realiti: bapa dan pendidik yang menulis tentang isu semasa dari sudut ibu bapa."
    ld = {"@context": "https://schema.org", "@type": "Person", "name": AUTHOR, "url": f"{SITE_URL}/tentang.html",
          "sameAs": [THREADS_URL]}
    page = head(f"Tentang {AUTHOR} | {SITE_NAME}", desc, "tentang.html",
                f'<meta property="og:type" content="profile">\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    page += f"""<body class="page-about">
{header('', 'tentang')}
<main id="utama" class="wrap-narrow about">
  <span class="avatar avatar-lg" aria-hidden="true">ZR</span>
  <h1>Tentang {AUTHOR}</h1>
  <p class="standfirst">Bapa, pendidik, dan penulis Parenting Realiti.</p>
  <div class="article-body">
    <p>Setiap hari saya bersama kanak-kanak, sama ada di rumah atau dalam kerja saya dalam bidang pendidikan. Dari situ saya belajar satu perkara: kebanyakan ibu bapa tidak kekurangan maklumat. Kita kekurangan masa untuk menapis maklumat itu dan memutuskan apa yang perlu dibuat.</p>
    <p>Parenting Realiti bermula sebagai thread di Threads. Setiap kali ada berita yang menyentuh keselamatan, pendidikan atau kesihatan anak-anak, saya cuba menjawab satu soalan mudah: apa langkah yang boleh kita ambil malam ini?</p>
    <h2>Prinsip penulisan</h2>
    <ul>
      <li>Fakta disemak dengan sekurang-kurangnya dua portal berita utama, dan pautan sumber diletakkan di hujung artikel.</li>
      <li>Privasi mangsa dijaga. Nama kanak-kanak dan keluarga yang terlibat dalam berita tidak disiarkan.</li>
      <li>Tiada menuding jari. Tujuannya membantu ibu bapa lain bersedia, bukan menyalahkan sesiapa.</li>
      <li>Panduan di sini bersifat umum. Untuk keadaan anda sendiri, rujuk doktor, guru atau pihak berkuasa.</li>
    </ul>
    <h2>Hubungi dan ikuti</h2>
    <p>Thread baharu diterbitkan hampir setiap hari. Ikuti saya di <a href="{THREADS_URL}" target="_blank" rel="noopener">Threads (@zullkarrnain)</a> dan kongsikan tips anda di ruangan komen.</p>
  </div>
</main>
{footer('')}
{SCRIPT}
</body>
</html>"""
    (OUT / "tentang.html").write_text(page, encoding="utf-8")


def build_seo(arts):
    urls = [(f"{SITE_URL}/", arts[-1]["date"]), (f"{SITE_URL}/tentang.html", arts[-1]["date"])]
    urls += [(f"{SITE_URL}/artikel/{a['slug']}.html", a["date"]) for a in arts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    sm += "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "artikel").mkdir(parents=True)
    shutil.copy(ROOT / "style.css", OUT / "style.css")
    text = SRC.read_text(encoding="utf-8")
    n = len(re.findall(r"^## Artikel \d+: ", text, flags=re.M))
    if n != len(META):
        raise SystemExit(f"Ralat: {n} artikel dalam artikel.md tetapi {len(META)} dalam artikel.json")
    arts = parse_articles(text)
    for a in arts:
        build_article(a, arts)
    build_index(arts)
    build_about(arts)
    build_seo(arts)
    host = re.sub(r"^https?://", "", SITE_URL).split("/")[0]
    if not host.endswith("github.io"):
        (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Siap: {len(arts)} artikel -> {OUT}")


if __name__ == "__main__":
    main()
