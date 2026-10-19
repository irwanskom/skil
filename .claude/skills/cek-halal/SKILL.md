---
name: cek-halal
description: Cek status sertifikat halal di situs BPJPH (bpjph.halal.go.id) untuk satu atau beberapa nomor registrasi/sertifikat halal, nama usaha, atau nama produk, lalu tampilkan hasilnya sebagai tabel dan simpan ke CSV. Gunakan ketika pengguna meminta cek, cari, atau verifikasi sertifikat halal, nomor ID halal (mis. ID3211...), atau produk/produsen bersertifikat halal.
---

# Cek Sertifikat Halal BPJPH

Skrip: `cek-halal/cek_halal.py` di root repo ini (dua folder di atas `${CLAUDE_SKILL_DIR}/..`).
Situs BPJPH hanya bisa diakses dari komputer pengguna (jaringan Indonesia), bukan dari sesi cloud.
Kalau situs tidak bisa dibuka (403, DNS gagal), beri tahu pengguna untuk menjalankan Claude Code di komputernya sendiri.

## Langkah

1. Kumpulkan kata kunci dari permintaan pengguna: nomor registrasi, nama usaha, atau nama produk.
   Untuk lebih dari ~5 kata kunci, tulis ke `cek-halal/daftar.txt` (satu per baris).
2. Cari Python yang berjalan, berurutan: `py -3`, `python`, `python3`.
   Kalau Playwright belum ada (`No module named playwright` / pesan "Playwright belum terpasang"),
   jalankan `<python> -m pip install playwright`, lalu ulangi.
3. Jalankan dari root repo, selalu dengan `--headless` (input interaktif tidak bisa dijawab dari Claude):
   ```bash
   py -3 "${CLAUDE_SKILL_DIR}/../../../cek-halal/cek_halal.py" "ID32110081424521026" "Nama Usaha" --headless --out cek-halal/hasil
   py -3 "${CLAUDE_SKILL_DIR}/../../../cek-halal/cek_halal.py" cek-halal/daftar.txt --headless --out cek-halal/hasil
   ```
   Jangan turunkan `--delay` di bawah 4 detik.
4. Baca file CSV terbaru di `cek-halal/hasil/` dan tampilkan ke pengguna sebagai tabel:
   kata kunci, produk, produsen, nomor sertifikat, tanggal. Abaikan kolom `NOMOR` (nomor urut baris).
   Sebutkan kata kunci yang tidak ditemukan, dan beri path file CSV-nya.

## Kalau hasilnya tidak rapi

- `sumber` = `teks` atau `error`: jalankan lagi kata kunci itu dengan `--inspect` (tanpa `--headless` kalau pengguna di depan komputer),
  lalu baca `debug/inputs.json`, `debug/requests.json`, dan `debug/screenshot.png` untuk melihat struktur halaman
  dan sesuaikan `cek_halal.py`.
- Pesan captcha: minta pengguna menjalankan skrip sendiri tanpa `--headless` dan mengisi captcha di jendela browser.
