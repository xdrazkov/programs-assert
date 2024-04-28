
# Úkol 8: Je v programu chyba?
Uvažujme programy v jednoduchém imperativním programovacím jazyce, který podporuje jen přiřazení, podmínky a volání funkce input(), která může vrátit libovolnou hodnotu. Na konci každého programu je výstupní podmínka (uvozená assert), která popisuje, co by mělo platit po skončení programu. Vaším úkolem je napsat nástroj, který pro co nejvíc programů správně rozhodne, jestli zadaná výstupní podmínka po skončení programu vždy platí, nebo jestli někdy neplatí.

**Příklady programů:**
* x = 3
y = x + 5
assert x < 10 # platí
* x = input()
y = 10
if x > 0 then
y = y - x
end
assert y > 5 # neplatí (např. pro x = 10)
* x = input()
y = x * x
z = y + 10
assert z > 9 # platí

Archiv se všemi soutěžními programy najdete na adrese https://www.fi.muni.cz/~xjonas/studentCompetition/programs.zip

**Specifikace jazyka programů**: Použitý programovací jazyk je opravdu jednoduchý. Jediné aritmetické operace jsou sčítání (+), odčítání (-) a násobení (*). Porovnávací operátory jsou ==, !=, >=, <=, > a <. Argumenty aritmetických operací a porovnání mohou být jen číselné konstanty (nezáporná čísla od 0 do 1000) a proměnné (řetězce malých písmen anglické abecedy). Všechny proměnné reprezentují celá čísla neomezené velikosti. Podmínky (if…then…end) nemohou být zanořené, tj. tělo každé podmínky obsahuje jen sekvenci přiřazovacích příkazů. Jazyk neobsahuje žádné cykly ani goto příkazy.

**Poznámky a tipy:**

* Výběr programovacího jazyka necháváme na vás, ale preferujeme Python nebo C++. Pokud budete programovat v jazyce Python, může se vám hodit parser zadaného jazyka programů, který naleznete zde: https://www.fi.muni.cz/~xjonas/studentCompetition/parser.zip
* Neočekává se od vás, že váš program zvládne správně rozhodnout platnost všech výstupních podmínek; cílem je rozhodnout správně co nejvíce z nich. Některé programy jsou totiž opravdu těžké na analýzu. Některé jsou naopak poměrně lehké a na jejich rozhodnutí není potřeba nic sofistikovaného.
