"""Phase names and page schema used in the Board instructions. Existing providers re-export their original names."""


PHASES = ("new", "talk", "spec", "work", "done")


SCHEMA = "3"                                       # the Board's schema as pages carry it (decisions §255.12; 2: a *Done when* line may carry its proof, §257.4; 3: a party's section may hold *Talk* and *Accepted*, §258.6). A page of 1 or 2 is read as it is; the Board writes 3 when it next writes it

