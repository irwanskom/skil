# skil — plugin Claude Code

Plugin Claude Code berisi dua skill:

| Skill | Fungsi |
|---|---|
| `ui-ux-pro-max` | Panduan desain UI/UX (gaya, warna, font, aturan UX) untuk website dan aplikasi |
| `design-taste-frontend` | Desain landing page, portofolio, dan redesign yang tidak terlihat template (sumber: Leonxlnx/taste-skill, MIT) |
| `cek-halal` | Cek status sertifikat halal di situs BPJPH dari nomor registrasi, nama usaha, atau produk |

## Pasang (sekali saja)

Di Claude Code, ketik:

```
/plugin marketplace add irwanskom/skil
/plugin install skil@irwanskom
```

Lalu tutup dan buka lagi Claude Code. Kedua skill aktif di folder mana pun.

## Update

```
/plugin marketplace update irwanskom
```

## Kebutuhan

- Python 3.8+ (`py --version`)
- Untuk `cek-halal`: `py -m pip install playwright`, dan Claude Code dijalankan di komputer
  dengan internet Indonesia (situs BPJPH tidak bisa dibuka dari sesi cloud).
