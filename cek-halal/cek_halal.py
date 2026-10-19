"""Cek sertifikat halal di situs BPJPH (bpjph.halal.go.id) untuk daftar kata kunci.

Setiap baris di file input berisi satu nomor registrasi, nama usaha, atau nama produk.
Skrip membuka halaman pencarian BPJPH di Chrome/Edge, mencari setiap kata kunci,
lalu menyimpan hasilnya ke CSV (bisa dibuka di Excel).

Data diambil dari respons API situs (paling rapi) dan, kalau tidak ada, dari tabel
atau teks di halaman.

Pemakaian (Windows):
    py cek_halal.py daftar.txt               # cek semua baris di daftar.txt
    py cek_halal.py ID321100... "Toko Ani"   # atau langsung kata kuncinya
    py cek_halal.py daftar.txt --inspect     # mode pengintai: hanya baris pertama,
                                             # simpan HTML, screenshot, dan daftar
                                             # request jaringan ke folder debug/
Opsi:
    --delay 4        jeda (detik) antar-pencarian, default 4
    --headless       jalankan tanpa jendela browser
    --out FOLDER     folder hasil, default hasil/
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    from playwright.sync_api import TimeoutError as PWTimeout
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Playwright belum terpasang. Jalankan:  py -m pip install playwright")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get("CEK_HALAL_URL", "https://bpjph.halal.go.id/cari/sertifikat")
SITE_HOST = os.environ.get("CEK_HALAL_HOST", "halal.go.id")
CAPTCHA_SELECTORS = (
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    "iframe[src*='challenges.cloudflare.com']",
    ".g-recaptcha",
    ".h-captcha",
    ".cf-turnstile",
)
# Kolom pencarian yang paling mungkin, dicoba berurutan.
SEARCH_INPUT_SELECTORS = (
    "input[name*='regis' i]",
    "input[name*='search' i]",
    "input[name*='keyword' i]",
    "input[name*='cari' i]",
    "input[type='search']",
    "input[placeholder*='cari' i]",
    "input[placeholder*='nama' i]",
    "input[placeholder*='nomor' i]",
    "input[type='text']",
)


def looks_like_reg_number(text):
    """Nomor registrasi BPJPH berupa kode panjang berisi angka (mis. ID3111000...)."""
    compact = re.sub(r"[\s\-/.]", "", text)
    return len(compact) >= 10 and sum(c.isdigit() for c in compact) >= 8


def launch_browser(pw, headless):
    override = os.environ.get("CEK_HALAL_BROWSER")
    if override:
        return pw.chromium.launch(executable_path=override, headless=headless)
    # Pakai Chrome atau Edge yang sudah ada di Windows, jadi tidak perlu unduh browser.
    for channel in ("chrome", "msedge"):
        try:
            return pw.chromium.launch(channel=channel, headless=headless)
        except Exception:
            continue
    try:
        return pw.chromium.launch(headless=headless)
    except Exception:
        sys.exit("Chrome/Edge tidak ditemukan. Jalankan:  py -m playwright install chromium")


def wait_for_captcha(page, headless):
    if not any(page.locator(sel).count() for sel in CAPTCHA_SELECTORS):
        return
    if headless:
        print("  ! Ada captcha. Jalankan ulang tanpa --headless untuk mengisinya.")
        return
    input("  ! Ada captcha di browser. Selesaikan dulu, lalu tekan Enter di sini... ")


def find_search_input(page):
    for sel in SEARCH_INPUT_SELECTORS:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            if el.is_visible() and el.is_enabled():
                return el
    return None


def biggest_record_list(data):
    """Cari list of dict terbesar di dalam JSON (biasanya daftar hasil pencarian)."""
    best = []
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            if node and all(isinstance(x, dict) for x in node) and len(node) > len(best):
                best = node
            stack.extend(node)
        elif isinstance(node, dict):
            stack.extend(node.values())
    return best


def flatten(record, prefix=""):
    flat = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(flatten(value, f"{name}."))
        elif isinstance(value, list):
            flat[name] = json.dumps(value, ensure_ascii=False)
        else:
            flat[name] = value
    return flat


def table_rows(page):
    rows = page.eval_on_selector_all(
        "table",
        """tables => tables.map(t => {
            const head = [...t.querySelectorAll('thead th, tr:first-child th')]
                .map(th => th.innerText.trim());
            const body = [...t.querySelectorAll('tbody tr')]
                .map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.trim()))
                .filter(r => r.length);
            return {head, body};
        })""",
    )
    records = []
    for table in rows:
        head = table["head"]
        for cells in table["body"]:
            names = head if len(head) == len(cells) else [f"kolom_{i + 1}" for i in range(len(cells))]
            records.append(dict(zip(names, cells)))
    return records


def search(page, query, headless, captured):
    """Jalankan satu pencarian, kembalikan (sumber, daftar_record)."""
    captured.clear()
    if looks_like_reg_number(query):
        page.goto(f"{BASE_URL}?no_regis={quote(query)}", wait_until="domcontentloaded")
    else:
        if not page.url.startswith(BASE_URL):
            page.goto(BASE_URL, wait_until="domcontentloaded")
        wait_for_captcha(page, headless)
        box = find_search_input(page)
        if box is None:
            page.goto(f"{BASE_URL}?no_regis={quote(query)}", wait_until="domcontentloaded")
        else:
            captured.clear()
            box.fill(query)
            box.press("Enter")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PWTimeout:
        pass
    wait_for_captcha(page, headless)

    for body in reversed(captured):
        records = biggest_record_list(body)
        if records:
            return "api", [flatten(r) for r in records]
    records = table_rows(page)
    if records:
        return "tabel", records
    text = page.locator("main").inner_text() if page.locator("main").count() else page.inner_text("body")
    return "teks", [{"teks_halaman": " ".join(text.split())[:2000]}]


def save_debug(page, requests_log, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "page.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(out_dir / "screenshot.png"), full_page=True)
    inputs = page.eval_on_selector_all(
        "input, select, textarea, button",
        """els => els.map(e => ({tag: e.tagName.toLowerCase(), type: e.type || '',
            name: e.name || '', id: e.id || '', placeholder: e.placeholder || '',
            text: (e.innerText || e.value || '').trim().slice(0, 80)}))""",
    )
    (out_dir / "inputs.json").write_text(json.dumps(inputs, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "requests.json").write_text(json.dumps(requests_log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFile pengintai tersimpan di: {out_dir.resolve()}")
    print("Kirim isi folder itu (page.html, inputs.json, requests.json, screenshot.png) ke Claude.")


def write_csv(rows, path):
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    # utf-8-sig supaya Excel membaca huruf dengan benar.
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Cek sertifikat halal BPJPH dari daftar kata kunci.")
    parser.add_argument(
        "input", nargs="+",
        help="file .txt (satu kata kunci per baris) atau langsung nomor registrasi / nama usaha / produk",
    )
    parser.add_argument("--inspect", action="store_true", help="mode pengintai (baris pertama saja)")
    parser.add_argument("--delay", type=float, default=4.0, help="jeda antar-pencarian (detik)")
    parser.add_argument("--headless", action="store_true", help="tanpa jendela browser")
    parser.add_argument("--out", default="hasil", help="folder hasil")
    args = parser.parse_args()

    queries = []
    for item in args.input:
        if Path(item).is_file():
            lines = Path(item).read_text(encoding="utf-8-sig").splitlines()
            queries += [q.strip() for q in lines if q.strip() and not q.strip().startswith("#")]
        else:
            queries.append(item.strip())
    if not queries:
        sys.exit("Tidak ada kata kunci untuk dicek.")
    if args.inspect:
        queries = queries[:1]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    captured, requests_log, rows = [], [], []

    with sync_playwright() as pw:
        browser = launch_browser(pw, args.headless)
        page = browser.new_page(locale="id-ID")

        def on_response(resp):
            ctype = resp.headers.get("content-type", "")
            entry = {"url": resp.url, "method": resp.request.method, "status": resp.status, "type": ctype}
            if resp.request.post_data:
                entry["post_data"] = resp.request.post_data[:500]
            requests_log.append(entry)
            if "json" in ctype and SITE_HOST in urlparse(resp.url).netloc:
                try:
                    captured.append(resp.json())
                except Exception:
                    pass

        page.on("response", on_response)

        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {query}")
            try:
                source, records = search(page, query, args.headless, captured)
            except Exception as exc:
                source, records = "error", [{"error": str(exc)[:300]}]
            print(f"  -> {len(records)} baris dari {source}")
            for rec in records:
                rows.append({"kata_kunci": query, "sumber": source, **rec})
            if args.inspect:
                save_debug(page, requests_log, Path("debug"))
            elif i < len(queries):
                time.sleep(args.delay)

        browser.close()

    result = out_dir / f"hasil_{datetime.now():%Y%m%d_%H%M}.csv"
    write_csv(rows, result)
    print(f"\nSelesai. Hasil: {result.resolve()}")


if __name__ == "__main__":
    main()
