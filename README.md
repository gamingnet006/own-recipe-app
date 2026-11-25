# Kochheft · Cookbook

A free, self-hosted recipe app and website for families: recipes in by link, text, photo or share sheet, a shopping
list with tiles and Siri, a week plan, cook mode with timers, allergen hints and nutrition estimates. German and
English (in English the app is called **Cookbook**). Runs in Docker on a Raspberry Pi, a Mac or any Linux machine.

**Deutsch:** Eine kostenlose, selbst gehostete Rezept-App und Webseite für die Familie: Rezepte per Link, Text, Foto
oder Teilen, Einkaufsliste mit Kacheln und Siri, Wochenplan, Kochmodus mit Timern, Allergen-Hinweise und
Nährwert-Schätzung. Auf Deutsch und Englisch.

**Documentation, installation and everything else:** [docs/kh/README.md](docs/kh/README.md) (Deutsch und English) ·
[Changelog](docs/kh/CHANGELOG.md)

## Based on Mealie

Kochheft is a modified fork of [Mealie](https://github.com/mealie-recipes/mealie) by Hayden and the Mealie
contributors. All of Mealie's code, its copyright and its license stay in place; Kochheft's own parts live in folders
named `kh`, and every change to Mealie's files is marked with a `KH:` comment. Kochheft is an independent project and
is **not affiliated with or endorsed by Mealie**. Problems with Kochheft belong here, not to the Mealie project.

## License

[GNU Affero General Public License v3.0](LICENSE), like Mealie. Anyone who uses a Kochheft installation over the
network can get its source code: **More → About** links to this repository. Third-party parts and their licenses:
[docs/kh/THIRD_PARTY_NOTICES.md](docs/kh/THIRD_PARTY_NOTICES.md).

## No warranty

Kochheft is provided as is, without any warranty (sections 15 and 16 of the license). Allergen and nutrition
information is **estimated from the ingredient text and may be wrong or incomplete**; it never replaces reading the
package or medical advice. You run your own installation and are responsible for it, its backups and who can reach it.

**Deutsch:** Ohne Gewähr. Allergene und Nährwerte werden aus dem Zutatentext geschätzt und können falsch oder
unvollständig sein; sie ersetzen nie den Blick auf die Packung oder ärztlichen Rat. Wer Kochheft betreibt, ist für die
eigene Installation, ihre Backups und den Zugang selbst verantwortlich.

## Privacy

No telemetry. Recipes, photos and accounts stay on your own machine; what leaves it (for example to an AI provider you
choose) is listed in the README table "Was geht wohin · What goes where". No credentials, passwords or keys are stored
in this repository; configuration uses placeholders in [`kh/ops/.env.example`](kh/ops/.env.example).

## Built with Claude Code

Kochheft was planned and written with [Claude Code](https://claude.com/claude-code), Anthropic's coding assistant,
working with the project's owner. The plan, the decisions and the rules it followed are public:
[PLAN.md](PLAN.md) · [PLAN.en.md](PLAN.en.md) · [.claude/CLAUDE.md](.claude/CLAUDE.md). Commits written with it carry a
`Co-Authored-By: Claude` line.

## Security

Please report vulnerabilities privately, see [SECURITY.md](SECURITY.md).
