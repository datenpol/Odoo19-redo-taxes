# Datenpol Euro Demo in Codex

Diese Anleitung ist für Vertrieb und Pre-Sales gedacht. Ihr müsst dafür nicht coden.

Wenn Codex, der Skill und eure Odoo-Demo sauber vorbereitet sind, besteht der eigentliche Ablauf am Ende aus genau einem Befehl.

## Kurz gesagt

Der Skill `datenpol-euro-demo` macht aus einer frischen Odoo-19-Demoumgebung eine österreichisch wirkende Präsentationsumgebung.

Wichtig dabei:

- Der Skill arbeitet auf einer bestehenden Odoo-19-Demo.
- Er ist für Demo und Präsentation gedacht, nicht für echte Buchhaltungsmigration.
- Ihr braucht die Root-URL der Umgebung und einen API-Key aus Odoo.

## Einmalig einrichten

Diese Schritte macht ihr in der Regel nur einmal auf eurem Rechner:

1. Ladet die Codex App herunter.
2. Installiert die Codex App.
3. Meldet euch mit eurem ChatGPT-Account an.
4. Installiert den Skill in Codex:

```text
$skill-installer https://github.com/datenpol/Odoo19-redo-taxes
```

5. Startet Codex nach der Installation einmal neu.

## Pro neue Demo

Für jede neue Odoo-Demoumgebung geht ihr so vor:

1. Legt lokal einen neuen Projektordner an, zum Beispiel `C:\Odoo-Demos\kunde-a`.
2. Öffnet den Ordner in der Codex App.
3. Wechselt in den Browser.
4. Legt auf `.odoo19.at` eine neue Odoo-19-Demoumgebung an.
5. Installiert die für euren Termin relevanten Module.
6. Meldet euch im Zielsystem mit dem gewünschten Admin-User an.
7. Aktiviert den Developer Mode, falls der Punkt `Account Security` noch nicht sichtbar ist.
8. Öffnet im Benutzer-Menü `My Profile / Preferences` und geht auf `Account Security`.
9. Klickt auf `New API Key`, vergebt einen verständlichen Namen und kopiert den Key sofort weg.

Wichtig:

- Der API-Key wird nur bei der Erstellung angezeigt.
- Der API-Key ist persönlich und hat die Rechte eures Benutzers.
- Für den Standardfall im Demo-Setup verwendet ihr den Key des Admin-Users.

## Skill ausführen

Wechselt zurück in die Codex App und führt den Skill mit URL und API-Key aus:

```text
$datenpol-euro-demo https://meinedemo.odoo19.at <API_KEY>
```

Wichtig:

- Verwendet die Root-URL der Instanz, normalerweise ohne `/odoo`.
- Der API-Key gehört als zweiter Wert in den Befehl.
- Wenn der Skill nicht gefunden wird, ist er meist noch nicht installiert oder Codex wurde nach der Installation noch nicht neu gestartet.

## Danach

1. Wartet, bis Codex die Ausführung abgeschlossen hat.
2. Prüft die Bestätigung in Codex.
3. Wechselt zurück in den Browser.
4. Aktualisiert die Odoo-Seite und schaut euch die Umgebung an.

## Woran ihr erkennt, dass es geklappt hat

Typischerweise seht ihr danach eine deutlich österreichischere Demooberfläche, zum Beispiel bei:

- Firmendaten
- Journals
- Steuerbezeichnungen
- Kontenbezeichnungen
- weiteren sichtbaren Buchhaltungsdetails

## Wenn etwas nicht klappt

`Account Security` fehlt:
Developer Mode ist noch nicht aktiv.

`API-Key funktioniert nicht`:
Meist wurde der falsche Key kopiert, der Key gehört zu einem anderen Benutzer oder der Key wurde nicht vollständig übernommen. In dem Fall einen neuen API-Key erzeugen.

`Skill nicht gefunden`:
Skill installieren und Codex neu starten.

`Keine Verbindung zur Odoo-Umgebung`:
URL prüfen. Meist ist die Instanz-URL falsch oder es wurde versehentlich `/odoo` mitkopiert.

## Empfohlener Standardsatz für den Workshop

Wenn alles vorbereitet ist, braucht ihr in Codex praktisch nur noch diesen einen Schritt:

```text
$datenpol-euro-demo https://meinedemo.odoo19.at <API_KEY>
```
