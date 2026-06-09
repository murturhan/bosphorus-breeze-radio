# Bosphorus Breeze Radio - Devir Raporu

## Proje Bilgisi

Proje adi: `bosphorus-breeze-radio`

GitHub repo:

<https://github.com/murturhan/bosphorus-breeze-radio>

Amac:

Oracle Cloud Free Tier uzerinde 24/7 YouTube canli radyo yayini yapmak.
Sistem FFmpeg ile `music/` klasorundeki ses dosyalarini okur, `assets/background.*`
dosyasini gorsel veya video arka plani olarak kullanir ve YouTube RTMP sunucusuna
yayin gonderir.

## Repo Durumu

Repo GitHub'a yuklendi ve asagidaki ana dosyalar eklendi:

- `install.sh`
- `stream.sh`
- `update_playlist.sh`
- `test_local.sh`
- `radio_admin.py`
- `.env.example`
- `systemd/bosphorus-radio.service`
- `systemd/bosphorus-radio-admin.service`
- `README.md`
- `music/`
- `assets/`
- `logs/`

## Yapilan Onemli Duzeltmeler

Ilk surumde FFmpeg ayarlari Oracle Free Tier icin fazla agirdi. Daha sonra yayin
varsayilanlari hafifletildi:

- Cozunurluk: `854x480`
- FPS: `24`
- Video bitrate: `900k`
- Encoder preset: `ultrafast`
- FFmpeg thread sayisi: `1`
- Ses: AAC `128k`

Ek olarak:

- `systemd` restart dongusu sinirlandi.
- Yayin servisi boot sirasinda otomatik baslamayacak sekilde duzenlendi.
- Admin panel servisi boot sirasinda baslayacak sekilde ayarlandi.
- Web admin panel eklendi.
- `test_local.sh` guvenli hale getirildi.
- README guvenli kurulum akisina gore guncellendi.
- Arka plan icin sadece JPG degil, resim ve video destegi eklendi.

## Arka Plan Destegi

Yeni desteklenen arka plan dosyalari:

- Resim: `assets/background.jpg`, `assets/background.jpeg`, `assets/background.png`
- Video: `assets/background.mp4`, `assets/background.mov`, `assets/background.webm`, `assets/background.mkv`

Davranis:

- Resim yuklenirse FFmpeg sabit gorsel olarak kullanir.
- Video yuklenirse FFmpeg videoyu otomatik donguye alir.
- Ayni anda birden fazla `background.*` varsa sistem oncelik sirasina gore ilk buldugunu kullanir.
- Web panelden yeni arka plan yuklenince eski `background.*` dosyalari temizlenir.

## Web Admin Panel

`radio_admin.py` ile basit bir web panel eklendi.

Panelin hedef fonksiyonlari:

- YouTube stream key girme
- Muzik yukleme
- Arka plan gorseli veya video yukleme
- Playlist yenileme
- Yayini baslatma
- Yayini durdurma
- Log goruntuleme

Panel servisi:

```bash
sudo systemctl start bosphorus-radio-admin.service
```

SSH tunnel:

```powershell
ssh -i "$env:USERPROFILE\Downloads\SSH_KEY_DOSYASI.key" -L 8788:127.0.0.1:8788 ubuntu@SUNUCU_PUBLIC_IP
```

Tarayici adresi:

```text
http://127.0.0.1:8788
```

## Oracle Cloud Durumu

Eski makine silindi.

Yeni makine olusturuldu fakat kritik bir hata var: yeni VM yanlislikla
**Oracle Linux 9** olarak acildi. Proje Ubuntu 24.04 icin hazirlanmistir.

Mevcut yeni VM bilgisi:

```text
Public IP: 92.5.123.201
OS: Oracle Linux 9
SSH username: opc
Shape: VM.Standard.E2.1.Micro
```

Bu makineye `ubuntu@92.5.123.201` ile baglanilamaz. Oracle Linux kullanici adi
`opc` olur:

```powershell
ssh -o ConnectTimeout=120 -i "$env:USERPROFILE\Downloads\ssh-key-2026-06-08.key" opc@92.5.123.201
```

Ancak bu makineyle devam edilmesi onerilmez.

## Onerilen Devam Yolu

En saglikli yol:

1. Mevcut Oracle Linux 9 VM silinsin.
2. Yeni VM su ayarlarla acilsin:
   - OS: `Canonical Ubuntu`
   - Version: `24.04`
   - Username: `ubuntu`
   - Shape: `VM.Standard.E2.1.Micro`
   - Public IPv4: enabled
   - SSH key indirilsin
3. Temiz kurulum yapilsin.

Kurulum komutlari:

```bash
sudo apt update
sudo apt install -y git ffmpeg python3
git clone https://github.com/murturhan/bosphorus-breeze-radio.git
cd bosphorus-breeze-radio
sudo ./install.sh
```

## Dikkat Edilecekler

- Oracle Free Tier E2 Micro 1080p yayin icin zayiftir.
- Varsayilan 480p ayarlar korunmalidir.
- Yayin baslatmadan once panelde guvenli test yapilmalidir.
- Ilk kurulumda canli yayin otomatik baslamamalidir.
- YouTube stream key asla GitHub'a commit edilmemelidir.
- `.env` sadece sunucuda kalmalidir.
- Muzikler `music/` icine yuklenmelidir.
- Arka plan resim veya video olabilir.
- Public IPv4 acik olmalidir.
- Ubuntu kullanici adi `ubuntu` olur.
- Oracle Linux kullanici adi `opc` olur.

## Yasanan Sorunlar

- Ilk kurulumda 1080p/30fps FFmpeg ayarlari Oracle Free Tier makineyi asiri yordu.
- Servis restart dongusune girince SSH baglantilari yavasladi ve zaman asimina dustu.
- `.env` dosyasini terminal/nano ile duzenlemek kullanici icin kotu deneyim oldu.
- Web panel en bastan eklenmedigi icin gereksiz ugras olustu.
- Yeni VM acilirken OS satiri kacirildi ve Ubuntu yerine Oracle Linux 9 acildi.

## Mevcut En Saglikli Sonuc

Kod tarafi GitHub uzerinde daha guvenli hale getirildi.

Altyapi tarafinda mevcut VM yanlis OS ile acildigi icin silinip Ubuntu 24.04 ile
yeniden acilmasi tavsiye edilir.
