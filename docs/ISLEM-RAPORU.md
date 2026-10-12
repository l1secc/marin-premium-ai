# Marin Premium AI — İşlem Raporu

**Tarih:** 12 Ekim 2026
**Sonuç repo:** <https://github.com/l1secc/marin-premium-ai>

## Ne yapıldı

`marin-premium` temasının **telifsiz kopyası** ayrı bir repo olarak kuruldu.
Tema, palet sistemi, araçlar ve config'ler birebir aynı; sadece duvar kağıtları
değişti.

1. **Orijinal tema analiz edildi:** tarayıcı, systemd servisi, palet üreteci ve
   görsel-renk türetme zinciri (`tools/marin_generate.py`).
2. **16 AI görsel üretildi:** anahtarsız, ücretsiz bir metinden-görsele servisi
   (Pollinations / `sana`) ile, Marin estetiğinde (sarışın, pembe tonlar,
   okul üniforması, çeşitli sahneler). 1. parti 6/12, 2. parti 10/10 başarılı.
3. **En iyi 10 seçildi**, filigran kırpıldı ve 1920×1080'e ölçeklendi:
   - 01 Çiçek Mevsimi
   - 02 Neon Gece
   - 03 Sonbahar
   - 04 Kar
   - 05 Yıldızlı Gece
   - 06 Sınıf
   - 07 Kafe
   - 08 Festival
   - 09 Çiçek Tarlası
   - 10 Sahil
4. **Paletler görsellerden yeniden üretildi:** her görsel için bir renk paleti
   (`palettes/01..10`), duvar kağıtları (`backgrounds/`) ve tema config'leri.
5. **Yeni GitHub reposu** oluşturuldu ve push edildi:
   `l1secc/marin-premium-ai` (public).

## Lisans durumu

- **Görsel dosyaları telifsiz:** tamamen yapay zekâ ile üretildi, **insan
  yazarı yok** → dosyalarda telif yok; kopyalama, değiştirme ve dağıtımda
  serbest, atıf gerekmez.
- **Hiçbir sanatçı/stok görseli bundle'lanmadı.**
- **Karakter notu:** *My Dress-Up Darling* ve Marin Kitagawa © Shinichi Fukuda /
  CloverWorks. Görseller resmî değil, sadece benzer estetikte özgün AI
  render'ları. Dosyalar serbest; karakter hakkı sahiplerinde.

## Kurulum

```bash
omarchy theme install https://github.com/l1secc/marin-premium-ai.git
omarchy theme set "Marin Premium Ai"
```

Galeride fotoğraf değiştirme:

```bash
marin-next          # sonraki görsel
marin-next sync     # arka planla paleti eşitle
```

## Sınırlamalar

- Görseller **yarı-gerçekçi** bir modelle üretildi (2D anime çizimi değil) ve
  çözünürlük üretimde ~1024×576'dan 1920×1080'e ölçeklendi; hafif yumuşaklık
  normaldir.
- Resmî Marin Kitagawa görseli **değildir**; karakter birebir değil, tema
  estetiği hedeflendi.
- Kaynak 1920×1080 görseller `sources/` altında; paletleri yeniden üretmek için:
  `python3 tools/marin_generate.py`.
