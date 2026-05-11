# MD-Lambda-View PWA — Installations- und Deployment-Anleitung

Diese PWA besteht aus drei HTML-Seiten (Startseite + 2D + 3D), einem
Manifest, einem Service Worker und einem Satz Icons.

## Schnellstart: Auf md-lambda-view.com hochladen

1. Lege auf Deinem Webhoster einen Unterordner an, z.B. `/app/`.
2. Lade **alle** Dateien aus dem ZIP dorthin hoch — die Ordnerstruktur
   muss erhalten bleiben (`/app/index.html`, `/app/icons/icon-192.png`, …).
3. **Wichtig:** Die Seite muss über HTTPS erreichbar sein, sonst
   funktioniert die PWA-Installation nicht (kein Service Worker auf HTTP).
   Auf Wix ist HTTPS standardmäßig aktiv.
4. Fertig — die App ist unter `https://md-lambda-view.com/app/` aufrufbar.

## Falls Wix verwendet wird

Wix erlaubt das direkte Hochladen statischer Dateien nur eingeschränkt.
Zwei Optionen:

- **Velo (Wix Code)**: über das Code-Modul HTML-Dateien als Static-Assets
  ablegen. Funktioniert, aber etwas fummelig — Service Worker müssen unter
  dem korrekten Scope laufen.
- **Subdomain mit anderem Hoster**: Lege eine Subdomain wie
  `app.md-lambda-view.com` an und hoste sie z.B. auf Netlify, Cloudflare
  Pages oder GitHub Pages — alle drei sind kostenlos für statische Seiten
  und bieten HTTPS out of the box. Hochladen per Drag & Drop des ZIPs.

Mein Tipp: **Cloudflare Pages** oder **Netlify**, dauert keine 10 Minuten.

## Auf dem Handy installieren

**Android (Chrome):**
1. `md-lambda-view.com/app/` aufrufen
2. Es erscheint automatisch der "App installieren"-Button — antippen.
3. Alternativ: Browser-Menü → "App installieren" / "Zum Startbildschirm".

**iPhone (Safari):**
1. `md-lambda-view.com/app/` in Safari aufrufen (nicht Chrome!)
2. Teilen-Symbol unten antippen (Quadrat mit Pfeil nach oben)
3. "Zum Home-Bildschirm" wählen
4. Bestätigen — fertig.

Nach der Installation startet die App als eigenes Fenster ohne
Browser-UI, mit MD-Lambda-View Icon im App-Switcher.

## Offline-Nutzung

Beim ersten Besuch über das Netz lädt der Service Worker:
- alle HTML/CSS/JS der App
- die Icons
- Chart.js und Plotly von CDN

Beim zweiten Aufruf läuft die App komplett ohne Internet — perfekt für
die Werkstatt.

## Aktualisieren

Wenn Du Änderungen veröffentlichst:
1. Dateien neu hochladen
2. In `sw.js` die `CACHE_VERSION` hochzählen, z.B. von `v1` auf `v2`
3. Der Service Worker erkennt das beim nächsten Aufruf und löscht den
   alten Cache automatisch.

Wenn Du das vergisst, sehen Nutzer noch die alte Version, bis der Cache
abläuft. Also nicht vergessen!

## Dateistruktur

```
app/
├── index.html              ← Startseite mit zwei Kacheln
├── 2d.html                 ← 2D-Auswertung TPS / λ
├── 3d.html                 ← 3D-Map RPM / TPS / λ
├── manifest.webmanifest    ← App-Metadaten
├── sw.js                   ← Service Worker (Offline-Cache)
└── icons/
    ├── icon-60.png         ← iOS Notification
    ├── icon-72.png         ← Android legacy
    ├── icon-76.png         ← iPad Home
    ├── icon-120.png        ← iPhone Home @2x
    ├── icon-152.png        ← iPad Home @2x
    ├── icon-167.png        ← iPad Pro
    ├── icon-180.png        ← iPhone Home @3x (primary iOS icon)
    ├── icon-192.png        ← Android Home
    ├── icon-256.png        ← Generic
    ├── icon-384.png        ← Android splash
    ├── icon-512.png        ← App Store / Android splash large
    ├── icon-maskable-192.png  ← Android adaptive icon
    └── icon-maskable-512.png  ← Android adaptive icon large
```

## Icon austauschen

Wenn Du ein eigenes Logo / Icon willst (z.B. das `cropped-md.png` aus
Deiner Website), brauchst Du die obigen 13 PNG-Dateien in den genannten
Größen. Tools wie [realfavicongenerator.net](https://realfavicongenerator.net)
oder [pwabuilder.com](https://pwabuilder.com) erzeugen die alle aus einem
einzelnen Hi-Res-Bild automatisch.

## Test der PWA-Konformität

Nach dem Hochladen kannst Du die App testen:
- Chrome DevTools → Lighthouse → "Progressive Web App" Kategorie auswählen
- pwabuilder.com → URL eingeben → bekommst einen vollständigen Report

Beides sollte grün sein. Falls nicht, sagen mir die Reports genau, was
fehlt.
