# Bosphorus Breeze Radio - Guncel Devir Raporu

Tarih: 2026-06-09

## Kisa Ozet

`bosphorus-breeze-radio` projesi, Oracle Cloud Free Tier uzerinde 24/7 YouTube
canli radyo yayini yapmak icin hazirlanmis bir FFmpeg tabanli sistemdir.

Repo GitHub'dadir:

<https://github.com/murturhan/bosphorus-breeze-radio>

Kod tarafi son durumda su hedefleri destekler:

- `music/` klasorundeki muzikleri okur.
- `mp3`, `m4a`, `wav` ses dosyalarini destekler.
- Playlist dosyasini otomatik uretir.
- YouTube RTMP adresine yayin gonderir.
- YouTube stream key bilgisini `.env` dosyasindan okur.
- Web admin panel ile stream key, muzik ve arka plan dosyasi yuklenebilir.
- Arka plan sadece resim degil, video da olabilir.
- `systemd` servisleri ile yeniden baslatma ve panel calistirma yapilir.

## Son Kodlama Durumu

Son kodlama asamasinda arka plan sistemi genisletildi.

Eski beklenti:

- Sadece `assets/background.jpg`

Yeni durum:

- Resim arka plan:
  - `assets/background.jpg`
  - `assets/background.jpeg`
  - `assets/background.png`
- Video arka plan:
  - `assets/background.mp4`
  - `assets/background.mov`
  - `assets/background.webm`
  - `assets/background.mkv`

Davranis:

- Resim dosyasi varsa FFmpeg sabit gorsel olarak kullanir.
- Video dosyasi varsa FFmpeg videoyu sonsuz donguye alir.
- Web panelden yeni arka plan yuklenince eski `assets/background.*` dosyalari
  temizlenir.
- FFmpeg baslamadan once arka plan dosyasinda video stream var mi kontrol edilir.
- Desteklenmeyen arka plan uzantisi yuklenirse panel reddeder.

## Guncellenen Ana Dosyalar

### `stream.sh`

Yayin baslatan ana script.

Son durum:

- `.env` kontrolu yapar.
- YouTube stream key bos veya varsayilan placeholder ise baslamaz.
- Muzik dosyasi yoksa baslamaz.
- Playlist yoksa otomatik uretir.
- Arka plan dosyasini `assets/background.*` olarak arar.
- Resim/video ayrimini dosya uzantisina gore yapar.
- Video arka plan icin `-stream_loop -1` kullanir.
- Oracle Free Tier icin daha hafif yayin ayarlari kullanir:
  - 854x480
  - 24 FPS
  - H264
  - AAC 128k
  - `ultrafast`
  - 1 thread

### `radio_admin.py`

Web admin panel.

Son durum:

- YouTube stream key kaydeder.
- Muzik yukler.
- Arka plan resim veya video yukler.
- Playlist yeniler.
- Yayini baslatir, durdurur, yeniden baslatir.
- Son loglari panelde gosterir.
- Servis durumunu, muzik sayisini, playlist durumunu ve arka plan durumunu
  gosterir.

Desteklenen panel yuklemeleri:

- Muzik: `.mp3`, `.m4a`, `.wav`
- Arka plan: `.jpg`, `.jpeg`, `.png`, `.mp4`, `.mov`, `.webm`, `.mkv`

### `test_local.sh`

Guvenli lokal test scripti.

Son durum:

- YouTube'a yayin gondermez.
- 5 saniyelik FFmpeg cikti testi yapar.
- Playlist uretimini test eder.
- Resim ve video arka planlari test edebilir.
- Ciktiyi `logs/local_test_output.mkv` dosyasina yazar.

### `install.sh`

Kurulum scripti.

Son durum:

- Ubuntu 24.04 uyumlu paketleri kurar.
- FFmpeg, Python ve gerekli araclari hazirlar.
- Dizinleri olusturur.
- `.env` dosyasini hazirlar.
- Systemd servislerini kurar.
- Admin panel servis bilgisini kurulum sonunda gosterir.
- Arka plan olarak resim veya video kullanilabilecegini belirtir.

### `README.md`

Kullanici dokumani.

Son durum:

- Kurulum adimlari sade hale getirildi.
- Oracle Free Tier icin daha gercekci uyarilar eklendi.
- Web panel kullanimi anlatildi.
- Resim ve video arka plan destekleri eklendi.
- Servis komutlari ve sorun giderme notlari eklendi.

### `DEVIR_RAPORU.md`

Onceki devir raporu.

Son durum:

- GitHub'a eklendi.
- Eski VM surecini ve Oracle Linux/Ubuntu karisikligini aciklar.

## GitHub'a Eklenen Son Degisiklikler

GitHub uzerinde su dosyalar guncellendi veya eklendi:

- `stream.sh`
- `radio_admin.py`
- `test_local.sh`
- `README.md`
- `install.sh`
- `DEVIR_RAPORU.md`
- `DEVIR_RAPORU_GUNCEL.md`

Bilinen commitler:

- `44d4d4e` - `stream.sh` video arka plan destegi
- `0438b13` - `radio_admin.py` video arka plan yukleme destegi
- `665b2af` - `test_local.sh` video arka plan test destegi
- `63c900d` - README guncellemesi
- `a7c9284` - installer guncellemesi
- `bdb4307` - eski devir raporu

## Bilinen Altyapi Durumu

Eski Oracle VM sorunluydu ve silindi.

Yeni VM acilirken kritik hata yapildi:

- Makine Ubuntu yerine Oracle Linux 9 olarak acildi.
- Oracle Linux 9 kullanici adi `opc` olur.
- Ubuntu 24.04 kullanici adi `ubuntu` olur.
- Bu proje Ubuntu 24.04 hedeflidir.

Son bilinen yanlis VM bilgisi:

```text
Public IP: 92.5.123.201
OS: Oracle Linux 9
SSH username: opc
Shape: VM.Standard.E2.1.Micro
```

Bu makine ile devam edilmesi onerilmez.

## Temiz Devam Icin Onerilen Yol

Yeni uygulama veya yeni gelistirici su adimlarla devam etmelidir:

1. Oracle Linux 9 acilan yanlis VM silinsin.
2. Yeni VM acilirken imaj kisminda mutlaka `Canonical Ubuntu 24.04` secilsin.
3. Shape olarak `VM.Standard.E2.1.Micro` secilsin.
4. Public IPv4 acik olsun.
5. SSH key indirilsin ve Windows tarafinda yetkileri duzeltilsin.
6. SSH kullanici adi `ubuntu` olarak kullanilsin.
7. Repo temiz makineye klonlansin.
8. `sudo ./install.sh` calistirilsin.
9. Admin panel tunnel ile acilsin.
10. Panelden stream key, muzik ve arka plan yuklensin.
11. Once lokal test, sonra canli yayin baslatilsin.

## Temiz Ubuntu Kurulum Komutlari

Ubuntu 24.04 makineye baglandiktan sonra:

```bash
sudo apt update
sudo apt install -y git ffmpeg python3
git clone https://github.com/murturhan/bosphorus-breeze-radio.git
cd bosphorus-breeze-radio
sudo ./install.sh
```

Admin paneli baslatmak:

```bash
sudo systemctl start bosphorus-radio-admin.service
```

Windows PowerShell uzerinden tunnel:

```powershell
ssh -o ConnectTimeout=120 -i "$env:USERPROFILE\Downloads\SSH_KEY_DOSYASI.key" -L 8788:127.0.0.1:8788 ubuntu@SUNUCU_PUBLIC_IP
```

Tarayicida:

```text
http://127.0.0.1:8788
```

## Test Sirasi

Yeni kurulumda canli yayina gecmeden once onerilen sira:

1. Panelden YouTube stream key kaydet.
2. En az bir muzik dosyasi yukle.
3. Resim veya video arka plan yukle.
4. Playlist yenile.
5. Sunucuda guvenli test calistir:

```bash
cd ~/bosphorus-breeze-radio
./test_local.sh
```

6. Test basariliysa panelden yayini baslat.
7. YouTube Studio'da veri gelip gelmedigini kontrol et.

## Dikkat Edilecek Kritik Noktalar

- YouTube stream key asla GitHub'a koyulmamali.
- `.env` dosyasi sadece sunucuda kalmali.
- Oracle Free Tier E2 Micro zayif oldugu icin 1080p onerilmez.
- Varsayilan 480p ayarlar korunmali.
- Yayin servisi boot ile otomatik baslatilmamali; once panelden kontrol edilmeli.
- Admin panel sadece SSH tunnel ile kullanilmali.
- Panel public internete acilmamali.
- Uzun veya agir video arka plan dosyalari CPU/disk kullanimi yaratabilir.
- Ilk testlerde kisa ve dusuk boyutlu video arka plan kullanilmali.

## Yasanan Sorunlardan Cikarilan Dersler

- Web panel en bastan gerekliydi; terminal uzerinden `.env` duzenlemek kullanici
  icin uygun degildi.
- Oracle Free Tier uzerinde 1080p/30fps ayarlar fazla riskli.
- Systemd restart limitleri olmadan servis donguye girerse SSH bile yavaslayabilir.
- Oracle'da imaj secimi kritik; Ubuntu yerine Oracle Linux secilirse kullanici adi
  ve kurulum akisi degisir.
- Kullaniciya her adimda tek tek ve ekran goruntusune gore yonlendirme gerekir.

## Mevcut Sonuc

Kod tarafi son istege gore tamamlandi:

- Arka planda resim de video da kullanilabilir.
- Web panel bu dosyalari yukleyebilir.
- FFmpeg yayin scripti video arka plani loop'a alabilir.
- README ve install bilgileri guncellendi.
- Devir icin bu guncel rapor hazirlandi.

Altyapi tarafinda temiz sonuc almak icin Ubuntu 24.04 ile yeni VM acilmasi
gereklidir.
