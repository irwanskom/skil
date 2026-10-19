# Cek Sertifikat Halal BPJPH

Mengecek status sertifikat halal di <https://bpjph.halal.go.id/cari/sertifikat>
untuk daftar nomor registrasi, nama usaha, atau nama produk, lalu menyimpan
hasilnya ke CSV (bisa dibuka di Excel).

## Persiapan (sekali saja, di Windows)

1. Python sudah terpasang (`py --version`).
2. Pasang Playwright:
   ```
   py -m pip install playwright
   ```
   Skrip memakai Chrome atau Edge yang sudah ada di Windows. Kalau keduanya
   tidak ada, jalankan `py -m playwright install chromium`.

## Pemakaian

1. Isi `daftar.txt`, satu kata kunci per baris.
2. Jalankan dari folder ini:
   ```
   py cek_halal.py daftar.txt
   ```
3. Hasil tersimpan di `hasil\hasil_TANGGAL_JAM.csv`.

Kalau muncul captcha, selesaikan di jendela browser lalu tekan Enter di Command Prompt.

| Opsi | Fungsi |
|---|---|
| `--inspect` | Mode pengintai: cek baris pertama saja dan simpan `page.html`, `inputs.json`, `requests.json`, `screenshot.png` ke folder `debug\` |
| `--delay 4` | Jeda antar-pencarian dalam detik (default 4, jangan terlalu kecil) |
| `--headless` | Jalankan tanpa jendela browser |
| `--out FOLDER` | Folder hasil (default `hasil`) |

## Cara kerja

- Kata kunci yang mirip nomor registrasi dibuka langsung lewat `?no_regis=...`.
- Kata kunci lain diketik ke kolom pencarian di halaman.
- Data diambil dari respons API situs (kolom paling lengkap). Kalau tidak ada,
  diambil dari tabel di halaman, dan terakhir dari teks halaman (kolom `teks_halaman`).
- Kolom `sumber` di CSV menunjukkan asal datanya: `api`, `tabel`, `teks`, atau `error`.

Gunakan dengan jeda yang wajar supaya tidak membebani server BPJPH.
