# Lokale KI (z. B. Ollama)

> **UNGETESTET, NICHT BESTÄTIGT.** Diese Anleitung beschreibt, wie es nach Mealies Einstellungen grundsätzlich gehen
> sollte. Niemand hat es mit Kochheft ausprobiert. Kochheft baut dafür nichts Eigenes; es ist nur Mealies
> KI-Anbieter, auf einen anderen Server gezeigt. Wenn es bei dir klappt oder nicht, schreib es bitte in ein Issue.

*English version below.*

## Was geht, was nicht

Mealie spricht mit KI-Anbietern über eine **OpenAI-kompatible Adresse**. Ollama bietet so eine Adresse an. Darum kann
Mealie (und damit Kochhefts Eingang für Fotos und Texte) im Prinzip an eine KI im eigenen Haus angeschlossen
werden. Dann verlassen Fotos und Texte das Haus nicht.

Die Qualität kann **niedriger** sein als bei den großen Cloud-Modellen: Zutaten und Mengen werden öfter falsch oder
gar nicht erkannt, Fotos von Handschrift klappen oft nicht. Prüfe jeden Entwurf in der Prüfansicht wie immer.

## Einrichten (Beispiel: Ollama auf einem anderen Rechner)

1. Auf dem Rechner mit Ollama: Ollama installieren und ein Modell laden.
   Für **Fotos** braucht es ein Modell mit Bildverständnis (ein „vision“-Modell), z. B. `ollama pull llama3.2-vision`.
   Für reine **Texte und Links** reicht ein normales Modell, z. B. `ollama pull llama3.1:8b`.
2. Ollama für andere Geräte im Heimnetz erreichbar machen. Standardmäßig hört es nur auf dem eigenen Rechner:
   `OLLAMA_HOST=0.0.0.0 ollama serve`
   (Nur im Heimnetz! Nie ungeschützt ins Internet stellen: Ollama hat keine Anmeldung.)
3. In Kochheft unter **Gruppe → KI-Anbieter** (das ist Mealies Seite) einen Anbieter anlegen:
   - **Basis-URL:** `http://<rechner>:11434/v1` (statt `<rechner>` der Name oder die IP des Rechners mit Ollama)
   - **Modell:** genau der Name aus `ollama list`, z. B. `llama3.2-vision`
   - **API-Schlüssel:** Das Feld darf nicht leer sein, Ollama prüft ihn aber nicht. Trag irgendein Wort ein, z. B. `ollama`.
   - **Zeitlimit:** auf einem schwachen Rechner hoch stellen (z. B. 600 Sekunden).
4. Mit dem Testknopf des Anbieters prüfen. Er zeigt auch, ob Bilder gehen.
5. In der Prioritätsliste nach oben schieben, wenn er zuerst gefragt werden soll.

### Ollama auf demselben Rechner wie Kochheft

Kochheft läuft in einem Container. Dort heißt „dieser Rechner“ nicht `localhost`, sondern
`host.docker.internal`. Basis-URL also: `http://host.docker.internal:11434/v1`.
Unter **Linux** (auch Raspberry Pi) muss der Mealie-Dienst in `kh/ops/docker-compose.yml` diesen Namen kennen:

```yaml
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Ollama muss dann auch für Container erreichbar sein (`OLLAMA_HOST=0.0.0.0`, siehe oben).

## Hardware

- Faustregel: Der Arbeitsspeicher (bei Apple-Chips der gemeinsame Speicher) muss etwa so groß sein wie das Modell
  plus 2 bis 4 GB. Ein 8-Milliarden-Modell braucht etwa 8 GB, ein Bildmodell eher 10 GB und mehr.
- Ein **Raspberry Pi ist dafür zu schwach.** Nimm einen Mac oder PC im Haus, am besten mit Grafikkarte oder Apple-Chip.
- Ohne Grafikkarte dauert ein Rezept aus einem Foto schnell mehrere Minuten.

## Datenschutz

Mit einer lokalen KI bleiben Fotos und Texte im Haus. Setze dafür in `.env` das Profil `lokal`
(`KH_PROFILE=lokal`): Dann warnt Kochheft, wenn noch ein Cloud-Anbieter mit Schlüssel eingetragen ist, und die
Spracherkennung läuft nur lokal. Die Zugangsdaten gehören nie ins Repository.

---

# Local AI (e.g. Ollama)

> **UNTESTED, NOT CONFIRMED.** This guide describes how it should work according to Mealie's settings. Nobody has
> tried it with Kochheft. Kochheft builds nothing of its own for it; it is only Mealie's AI provider pointed at
> another server. If it works for you or not, please say so in an issue.

## What works, what does not

Mealie talks to AI providers through an **OpenAI-compatible address**, and Ollama offers one. So Mealie (and with it
the intake for photos and texts) can in principle be connected to an AI in your own house. Photos and texts then never
leave it.

Quality can be **lower** than with the big cloud models: ingredients and amounts are misread or missed more often, and
photos of handwriting often fail. Check every draft in the review as always.

## Setting up (example: Ollama on another machine)

1. On the machine with Ollama: install it and pull a model. **Photos** need a model that understands images (a
   "vision" model), e.g. `ollama pull llama3.2-vision`. For **texts and links** a normal model such as
   `ollama pull llama3.1:8b` is enough.
2. Make Ollama reachable from other devices on your home network. By default it listens on its own machine only:
   `OLLAMA_HOST=0.0.0.0 ollama serve`
   (Home network only! Never expose it to the internet: Ollama has no login.)
3. In Kochheft under **Group → AI providers** (Mealie's page) add a provider:
   - **Base URL:** `http://<machine>:11434/v1` (name or IP of the machine running Ollama)
   - **Model:** exactly the name from `ollama list`, e.g. `llama3.2-vision`
   - **API key:** the field must not be empty, but Ollama does not check it. Enter any word, e.g. `ollama`.
   - **Timeout:** raise it on a weak machine (e.g. 600 seconds).
4. Use the provider's test button. It also shows whether images work.
5. Move it to the top of the priority list if it should be asked first.

### Ollama on the same machine as Kochheft

Kochheft runs in a container, where "this machine" is not `localhost` but `host.docker.internal`. So the base URL is
`http://host.docker.internal:11434/v1`. On **Linux** (also Raspberry Pi) the Mealie service in
`kh/ops/docker-compose.yml` must know that name:

```yaml
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Ollama must then also be reachable from containers (`OLLAMA_HOST=0.0.0.0`, see above).

## Hardware

- Rule of thumb: memory (shared memory on Apple chips) about the size of the model plus 2 to 4 GB. An 8-billion model
  needs about 8 GB, an image model more like 10 GB and up.
- A **Raspberry Pi is too weak** for this. Use a Mac or PC in the house, ideally with a graphics card or Apple chip.
- Without a graphics card one recipe from a photo quickly takes several minutes.

## Privacy

With a local AI, photos and texts stay in the house. Set the profile `lokal` in `.env` (`KH_PROFILE=lokal`): Kochheft
then warns while a cloud provider with a key is still set up, and speech recognition runs locally only. Credentials
never belong in the repository.
