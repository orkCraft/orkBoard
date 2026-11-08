// Whose table it is, by the race its colour comes from (spec 161 E, decisions §268.3): a party wears its race's colour, its leader a higher form of that race; the Orkmaster's is the table's warm wood. orkUI's `.ork-table`, `.ork-pennant`
// and `.ork-plate` take it as `data-party` (their race names), the sheets (look.css) as `data-race`. A party whose leader's head is a hero's (`hero-…`) or a race this file does not know takes its craft's by the party's slug; one it cannot place has
// none, and its table is the plain wood.
const BY_HEAD = { peon: "ork", shaman: "ork", elf: "elf", dryad: "elf", goblin: "goblin", imp: "goblin", gnome: "gnome", fairy: "gnome", knight: "knight", unicorn: "knight", skeleton: "undead", lich: "undead" };
const BY_SLUG = { tech: "ork", "game-design": "knight", game: "knight", product: "knight", design: "elf", art: "elf", release: "undead", run: "goblin", liveops: "goblin", marketing: "gnome", market: "gnome" };

/** The race colour of a party `g` (its leader's head, else its slug), "" when it has none. */
export const raceOf = (g) => BY_HEAD[String(g?.leader?.head?.race || "").split("-")[0]] || BY_SLUG[g?.slug] || "";

/** What `data-party` and `data-race` say for the open tab: the party's race, or `orkmaster` for the Orkmaster's. */
export const feltOf = (g) => (g ? raceOf(g) : "orkmaster");
