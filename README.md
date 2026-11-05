# Kraków SmartGrid: Autonomiczny Miejski System Dyspozytorski i Optymalizacji Ładowania Taboru Elektrycznego MPK Kraków

Oficjalny projekt zgłoszony do konkursu **„Open Data App”** organizowanego przez Centrum Obsługi Informatycznej Urzędu Miasta Krakowa (UMK 2026).

🌐 **Wersja Demonstracyjna Online (Live HTTPS):**  
👉 **[https://pioale.github.io/krakow-smartgrid/](https://pioale.github.io/krakow-smartgrid/)**

---

## 1. O projekcie

Kraków SmartGrid to platforma czasu rzeczywistego integrująca miejskie otwarte dane z autonomicznym algorytmem zarządzania przepływem energii (EMS - Energy Management System) oraz wielkoskalowym magazynem energii BESS LFP (2.0 MW / 4.0 MWh) na Zajezdni MPK Wola Duchacka.

System realizuje trójfilarową optymalizację kosztów energii Tauron B23:
1. **Ścięcie szczytu zapotrzebowania (Peak Shaving):** redukcja mocy zamówionej z 5.04 MW do 3.67 MW (-1.37 MW).
2. **Eliminacja opłaty mocowej URE:** w szczytowym oknie taryfowym (07:00–22:00 w dni robocze).
3. **Arbitraż taryfowy dzień/noc:** buforowanie taniej energii z nocnej doliny (380 zł/MWh) i oddawanie w szczycie wieczornym.

### Skala Projektu
- **Obiekt Pilotażowy (Zajezdnia Wola Duchacka):** 121 elektrobusów, 117 stacji ładowania, **795 721 zł rocznych oszczędności** (zwrot w 1.4 roku przy 70% dotacji FEnIKS).
- **Agregacja Miejska (10 Hubów w Krakowie):** bazy Wola Duchacka, Płaszów, Bieńczyce, zajezdnie tramwajowe Podgórze i Nowa Huta oraz huby szybkiego ładowania na pętlach miejskich: **3 580 000 zł rocznych oszczędności dla budżetu Krakowa**.

---

## 2. Wykorzystane Otwarte Dane Czasu Rzeczywistego (Real-Time Open Data)

1. **Zarząd Transportu Publicznego w Krakowie (ZTP GTFS-RT):**
   - Strumień telemetrii pozycji pojazdów na żywo: `https://gtfs.ztp.krakow.pl/VehiclePositions.pb`
   - Aktualizacje kursów i zjazdów do zajezdni: `https://gtfs.ztp.krakow.pl/TripUpdates.pb`
2. **Instytut Meteorologii i Gospodarki Wodnej (IMGW-PIB):**
   - Telemetria stacji synoptycznej Kraków-Balice: `https://danepubliczne.imgw.pl/api/data/synop/station/krakow` (dynamiczna korekta poboru mocy ogrzewania/klimatyzacji HVAC wg normy e-SORT).
3. **Polskie Sieci Elektroenergetyczne (PSE S.A. / TGE):**
   - Rynkowe ceny energii bilansującej RCE w cyklu 15-minutowym: `https://api.raporty.pse.pl/api/rce-pln`.

---

## 3. Autorzy

- **inż. Emil Oleksy** – Główny Inżynier Systemu, Absolwent AGH w Krakowie
- **Maja Majchrzak** – Analityk Danych i Projektant Efektywności Miejskiej
