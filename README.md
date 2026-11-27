# Parenting Realiti

Blog parenting oleh Zulkarnain Ramlan. Laman statik yang dibina daripada:

- `src/artikel.md`: teks penuh setiap artikel (`## Artikel N: tajuk`)
- `src/artikel.json`: domain laman dan metadata setiap artikel (slug, tarikh, topik), ikut urutan yang sama
- `style.css`: rupa laman
- `build.py`: menjana folder `site/`

Setiap push ke `main` akan menjana dan menerbitkan laman melalui GitHub Pages (`.github/workflows/pages.yml`).

Bina di komputer sendiri: `pip install markdown` kemudian `python build.py`.
