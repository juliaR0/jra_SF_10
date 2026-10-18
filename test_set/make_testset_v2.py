"""
BiAgram test set v2 generator.

Builds matched English–Spanish minimal-pair items for four features (articles, subject–verb agreement,
tense, auxiliaries) plus a code-switched part, following the rules in "BiAgram Test Set — Design Rules".

Every word form is written out by hand in the lexicon below (no automatic conjugation), so a native
speaker can check the lexicon once instead of checking thousands of generated sentences one by one.

Run:  python make_testset_v2.py            -> writes biagram_testset_v2.csv next to this file
"""
import csv, random, itertools, os

SEED = 2026
N_PER_FEATURE = 48          # items per feature per language (agreement/auxiliary: half singular, half plural)

# ---------------------------------------------------------------------------------------------
# LEXICON  (general Latin American Spanish, neutral vocabulary; general American English)
# ---------------------------------------------------------------------------------------------
# Subjects: (EN singular, EN plural, ES singular, ES plural, gender of the Spanish noun)
SUBJECTS = [
    ("The girl",    "The girls",    "La niña",       "Las niñas",       "f"),
    ("The boy",     "The boys",     "El niño",       "Los niños",       "m"),
    ("The teacher", "The teachers", "La maestra",    "Las maestras",    "f"),
    ("The neighbor","The neighbors","El vecino",     "Los vecinos",     "m"),
    ("The nurse",   "The nurses",   "La enfermera",  "Las enfermeras",  "f"),
    ("The cook",    "The cooks",    "El cocinero",   "Los cocineros",   "m"),
    ("The doctor",  "The doctors",  "La doctora",    "Las doctoras",    "f"),
    ("The farmer",  "The farmers",  "El agricultor", "Los agricultores","m"),
]

# Verb phrases. EN: base, 3sg present, past, -ing, past participle, complement.
# ES: infinitive, bare stem (a non-word on its own, and not an English word either, so the
#     omission foil cannot be mistaken for a code-switch), 3sg present, 3pl present, 3sg preterite,
#     3pl preterite, gerund, complement. Regular Spanish verbs only, so every form is predictable.
VERBS = [
    dict(key="walk",  en=("walk", "walks", "walked", "walking", "walked", "to the park"),
         es=("caminar", "camin", "camina", "caminan", "caminó", "caminaron", "caminando", "al parque"), transitive=False),
    dict(key="work",  en=("work", "works", "worked", "working", "worked", "at home"),
         es=("trabajar", "trabaj", "trabaja", "trabajan", "trabajó", "trabajaron", "trabajando", "en casa"), transitive=False),
    dict(key="cook",  en=("cook", "cooks", "cooked", "cooking", "cooked", "dinner"),
         es=("cocinar", "cocin", "cocina", "cocinan", "cocinó", "cocinaron", "cocinando", "la cena"), transitive=True),
    dict(key="clean", en=("clean", "cleans", "cleaned", "cleaning", "cleaned", "the kitchen"),
         es=("limpiar", "limpi", "limpia", "limpian", "limpió", "limpiaron", "limpiando", "la cocina"), transitive=True),
    dict(key="sweep", en=("sweep", "sweeps", "swept", "sweeping", "swept", "the floor"),
         es=("barrer", "barr", "barre", "barren", "barrió", "barrieron", "barriendo", "el piso"), transitive=True),
    dict(key="wash",  en=("wash", "washes", "washed", "washing", "washed", "the dishes"),
         es=("lavar", "lav", "lava", "lavan", "lavó", "lavaron", "lavando", "los platos"), transitive=True),
    dict(key="drink", en=("drink", "drinks", "drank", "drinking", "drunk", "water"),
         es=("beber", "beb", "bebe", "beben", "bebió", "bebieron", "bebiendo", "agua"), transitive=False),
    dict(key="buy",   en=("buy", "buys", "bought", "buying", "bought", "bread"),
         es=("comprar", "compr", "compra", "compran", "compró", "compraron", "comprando", "pan"), transitive=True),
    dict(key="sell",  en=("sell", "sells", "sold", "selling", "sold", "fruit"),
         es=("vender", "vend", "vende", "venden", "vendió", "vendieron", "vendiendo", "fruta"), transitive=True),
    dict(key="open",  en=("open", "opens", "opened", "opening", "opened", "the window"),
         es=("abrir", "abr", "abre", "abren", "abrió", "abrieron", "abriendo", "la ventana"), transitive=True),
    dict(key="write", en=("write", "writes", "wrote", "writing", "written", "a letter"),
         es=("escribir", "escrib", "escribe", "escriben", "escribió", "escribieron", "escribiendo", "una carta"), transitive=True),
    dict(key="answer",en=("answer", "answers", "answered", "answering", "answered", "the phone"),
         es=("contestar", "contest", "contesta", "contestan", "contestó", "contestaron", "contestando", "el teléfono"), transitive=True),
    dict(key="close", en=("close", "closes", "closed", "closing", "closed", "the door"),
         es=("cerrar", "cierr", "cierra", "cierran", "cerró", "cerraron", "cerrando", "la puerta"), transitive=True),
    dict(key="fix",   en=("fix", "fixes", "fixed", "fixing", "fixed", "the bike"),
         es=("arreglar", "arregl", "arregla", "arreglan", "arregló", "arreglaron", "arreglando", "la bicicleta"), transitive=True),
]

# Article items: object nouns. (EN noun, EN indefinite article, ES noun, ES gender, animate?)
NOUNS = [
    ("dog", "a", "perro", "m", True),      ("key", "a", "llave", "f", False),
    ("book", "a", "libro", "m", False),    ("box", "a", "caja", "f", False),
    ("coin", "a", "moneda", "f", False),   ("ring", "a", "anillo", "m", False),
    ("spoon", "a", "cuchara", "f", False), ("shoe", "a", "zapato", "m", False),
    ("eraser", "an", "borrador", "m", False), ("owl", "an", "búho", "m", True),
    ("apple", "an", "manzana", "f", False),("airplane", "an", "avión", "m", False),
    ("ant", "an", "hormiga", "f", True),   ("envelope", "an", "sobre", "m", False),
    ("insect", "an", "insecto", "m", True),("umbrella", "an", "paraguas", "m", False),
]
# Past-tense verbs for article items: (EN, ES 3sg preterite, allowed with animals?)
OBJ_VERBS = [("found", "encontró", True), ("saw", "vio", True),
             ("picked up", "recogió", False), ("hid", "escondió", False)]
LOCATIONS = [("in the garden", "en el jardín"), ("under the bed", "debajo de la cama"),
             ("near the door", "cerca de la puerta"), ("in the kitchen", "en la cocina")]

ANCHOR = {"present": ("every day", "todos los días"), "past": ("yesterday", "ayer"), "now": ("right now", "ahora")}
SWAP_EN_ART = {"a": "an", "an": "a"}
ES_ART = {"m": "un", "f": "una"}
SWAP_ES_ART = {"un": "una", "una": "un"}
ES_PRONOUN = {"m": "Él", "f": "Ella"}
ES_DEF = {"m": "el", "f": "la"}

# Code-switched determiner items: English noun after a Spanish definite article (gender of the Spanish translation)
CS_NOUNS = [(n_en, n_es, g) for n_en, _, n_es, g, animate in NOUNS if not animate][:12]

# ---------------------------------------------------------------------------------------------
rows = []
def add(item_id, frame_id, part, feature, correct, foils, **factors):
    for foil, foil_type, category in foils:
        assert foil != correct, (item_id, foil)
        rows.append(dict(pair_id=f"{item_id}-{foil_type}", item_id=item_id, frame_id=frame_id, part=part,
                         feature=feature, subject_number=factors.get("number", ""),
                         noun_gender=factors.get("gender", ""), en_article=factors.get("en_article", ""),
                         correct=correct, foil=foil, foil_type=foil_type, error_category=category, native_check=""))

rng = random.Random(SEED)
combos = [(si, vi) for si, vi in itertools.product(range(len(SUBJECTS)), range(len(VERBS)))
          if not (SUBJECTS[si][0] == "The cook" and VERBS[vi]["key"] == "cook")]   # avoid "The cook cooks dinner"

def sample_combos(n):
    c = combos[:]; rng.shuffle(c); return c[:n]

# 1. SUBJECT–VERB AGREEMENT (present, "every day")
for k, (si, vi) in enumerate(sample_combos(N_PER_FEATURE)):
    s, v, plural = SUBJECTS[si], VERBS[vi], k >= N_PER_FEATURE // 2
    base, s3, past, ing, pp, comp = v["en"]; inf, stem, p3s, p3p, pret3s, pret3p, ger, comp_es = v["es"]
    a_en, a_es = ANCHOR["present"]
    fid, num = f"AGR-{k+1:03d}", "pl" if plural else "sg"
    if not plural:
        subj = s[0]
        add(f"AGR-EN-{k+1:03d}", fid, "en", "verb_agreement", f"{subj} {s3} {comp} {a_en}.", [
            (f"{subj} {base} {comp} {a_en}.", "bare_stem", "omission"),
            (f"{subj} {ing} {comp} {a_en}.", "ing_form", "nonfinite")], number=num)
        subj = s[2]
        add(f"AGR-ES-{k+1:03d}", fid, "es", "verb_agreement", f"{subj} {p3s} {comp_es} {a_es}.", [
            (f"{subj} {p3p} {comp_es} {a_es}.", "wrong_number", "substitution"),
            (f"{subj} {stem} {comp_es} {a_es}.", "stem_nonword", "omission"),
            (f"{subj} {inf} {comp_es} {a_es}.", "infinitive", "nonfinite")], number=num, gender=s[4])
    else:
        subj = s[1]
        add(f"AGR-EN-{k+1:03d}", fid, "en", "verb_agreement", f"{subj} {base} {comp} {a_en}.", [
            (f"{subj} {s3} {comp} {a_en}.", "wrong_number", "substitution"),
            (f"{subj} {ing} {comp} {a_en}.", "ing_form", "nonfinite")], number=num)
        subj = s[3]
        add(f"AGR-ES-{k+1:03d}", fid, "es", "verb_agreement", f"{subj} {p3p} {comp_es} {a_es}.", [
            (f"{subj} {p3s} {comp_es} {a_es}.", "wrong_number", "substitution"),
            (f"{subj} {stem} {comp_es} {a_es}.", "stem_nonword", "omission"),
            (f"{subj} {inf} {comp_es} {a_es}.", "infinitive", "nonfinite")], number=num, gender=s[4])

# 2. TENSE (past with "yesterday"; singular only, because English plural present = bare stem)
for k, (si, vi) in enumerate(sample_combos(N_PER_FEATURE)):
    s, v = SUBJECTS[si], VERBS[vi]
    base, s3, past, ing, pp, comp = v["en"]; inf, stem, p3s, p3p, pret3s, pret3p, ger, comp_es = v["es"]
    a_en, a_es = ANCHOR["past"]; fid = f"TNS-{k+1:03d}"
    add(f"TNS-EN-{k+1:03d}", fid, "en", "tense", f"{s[0]} {past} {comp} {a_en}.", [
        (f"{s[0]} {s3} {comp} {a_en}.", "present_for_past", "substitution"),
        (f"{s[0]} {base} {comp} {a_en}.", "bare_stem", "omission"),
        (f"{s[0]} {ing} {comp} {a_en}.", "ing_form", "nonfinite")], number="sg")
    add(f"TNS-ES-{k+1:03d}", fid, "es", "tense", f"{s[2]} {pret3s} {comp_es} {a_es}.", [
        (f"{s[2]} {p3s} {comp_es} {a_es}.", "present_for_past", "substitution"),
        (f"{s[2]} {stem} {comp_es} {a_es}.", "stem_nonword", "omission"),
        (f"{s[2]} {inf} {comp_es} {a_es}.", "infinitive", "nonfinite")], number="sg", gender=s[4])

# 3. AUXILIARY (progressive, "right now")
for k, (si, vi) in enumerate(sample_combos(N_PER_FEATURE)):
    s, v, plural = SUBJECTS[si], VERBS[vi], k >= N_PER_FEATURE // 2
    base, s3, past, ing, pp, comp = v["en"]; inf, stem, p3s, p3p, pret3s, pret3p, ger, comp_es = v["es"]
    a_en, a_es = ANCHOR["now"]; fid, num = f"AUX-{k+1:03d}", "pl" if plural else "sg"
    en_subj, es_subj = (s[1], s[3]) if plural else (s[0], s[2])
    en_aux, en_wrong = ("are", "is") if plural else ("is", "are")
    es_aux, es_wrong = ("están", "está") if plural else ("está", "están")
    add(f"AUX-EN-{k+1:03d}", fid, "en", "auxiliary", f"{en_subj} {en_aux} {ing} {comp} {a_en}.", [
        (f"{en_subj} {ing} {comp} {a_en}.", "aux_dropped", "omission"),
        (f"{en_subj} {en_wrong} {ing} {comp} {a_en}.", "wrong_aux_number", "substitution")], number=num)
    add(f"AUX-ES-{k+1:03d}", fid, "es", "auxiliary", f"{es_subj} {es_aux} {ger} {comp_es} {a_es}.", [
        (f"{es_subj} {ger} {comp_es} {a_es}.", "aux_dropped", "omission"),
        (f"{es_subj} {es_wrong} {ger} {comp_es} {a_es}.", "wrong_aux_number", "substitution")], number=num, gender=s[4])

# 4. ARTICLES (indefinite object; each noun used 3 times)
art_combos = []
for ni, noun in enumerate(NOUNS):
    verbs_ok = [vj for vj, ov in enumerate(OBJ_VERBS) if ov[2] or not noun[4]]
    for _ in range(N_PER_FEATURE // len(NOUNS)):
        art_combos.append((rng.randrange(len(SUBJECTS)), rng.choice(verbs_ok), ni, rng.randrange(len(LOCATIONS))))
rng.shuffle(art_combos)
assert len(set(art_combos)) == len(art_combos), "duplicate article frames; change SEED"
for k, (si, vj, ni, li) in enumerate(art_combos):
    s, (v_en, v_es, _), (n_en, art_en, n_es, g, _), (l_en, l_es) = SUBJECTS[si], OBJ_VERBS[vj], NOUNS[ni], LOCATIONS[li]
    art_es = ES_ART[g]; fid = f"ART-{k+1:03d}"
    add(f"ART-EN-{k+1:03d}", fid, "en", "article", f"{s[0]} {v_en} {art_en} {n_en} {l_en}.", [
        (f"{s[0]} {v_en} {n_en} {l_en}.", "article_dropped", "omission"),
        (f"{s[0]} {v_en} {SWAP_EN_ART[art_en]} {n_en} {l_en}.", "a_an_swap", "substitution")], number="sg", en_article=art_en)
    add(f"ART-ES-{k+1:03d}", fid, "es", "article", f"{s[2]} {v_es} {art_es} {n_es} {l_es}.", [
        (f"{s[2]} {v_es} {n_es} {l_es}.", "article_dropped", "omission"),
        (f"{s[2]} {v_es} {SWAP_ES_ART[art_es]} {n_es} {l_es}.", "wrong_gender", "substitution")], number="sg", gender=g)

# 5. CODE-SWITCHED PART (Spanish matrix sentence; see Design Rules for evidence and caveats)
# 5a. Determiner + noun: Spanish determiner + English noun (preferred) vs English determiner + Spanish noun.
for k, (n_en, n_es, g) in enumerate(CS_NOUNS):
    s = SUBJECTS[k % len(SUBJECTS)]; v_en, v_es, _ = OBJ_VERBS[k % 2]; l_en, l_es = LOCATIONS[k % len(LOCATIONS)]
    add(f"CS-DET-{k+1:03d}", f"CS-DET-{k+1:03d}", "cs", "cs_det_noun", f"{s[2]} {v_es} {ES_DEF[g]} {n_en} {l_es}.", [
        (f"{s[2]} {v_es} the {n_es} {l_es}.", "english_det_spanish_noun", "switch")], gender=g)
# 5b. Auxiliary + verb: estar + English -ing (attested) vs haber + English participle (disallowed)
#     and vs English 'is' + Spanish gerund (rare / dispreferred).
trans = [v for v in VERBS if v["transitive"]]
for k, v in enumerate(trans):
    s = SUBJECTS[k % len(SUBJECTS)]
    base, s3, past, ing, pp, comp = v["en"]; inf, stem, p3s, p3p, pret3s, pret3p, ger, comp_es = v["es"]
    add(f"CS-AUX-{k+1:03d}", f"CS-AUX-{k+1:03d}", "cs", "cs_aux_verb", f"{s[2]} está {ing} {comp_es}.", [
        (f"{s[2]} ha {pp} {comp_es}.", "haber_english_participle", "switch"),
        (f"{s[2]} is {ger} {comp_es}.", "english_aux_spanish_gerund", "switch")], gender=s[4])
# 5c. Pronoun + verb (PILOT): full Spanish subject + English verb vs weak Spanish pronoun + English verb.
for k, v in enumerate(VERBS[:12]):
    s = SUBJECTS[k % len(SUBJECTS)]
    base, s3, past, ing, pp, comp = v["en"]
    add(f"CS-PRO-{k+1:03d}", f"CS-PRO-{k+1:03d}", "cs", "cs_pronoun_verb_pilot", f"{s[2]} {s3} {comp} {ANCHOR['present'][0]}.", [
        (f"{ES_PRONOUN[s[4]]} {s3} {comp} {ANCHOR['present'][0]}.", "pronoun_switch", "switch")], gender=s[4])

# ---------------------------------------------------------------------------------------------
# Automatic checks (Design Rules, quality control step 4)
ids = [r["pair_id"] for r in rows]
assert len(ids) == len(set(ids)), "duplicate pair_id"
items = {}
for r in rows:
    items.setdefault(r["item_id"], r)
frames = {}
for r in items.values():
    if r["part"] in ("en", "es"):
        frames.setdefault(r["frame_id"], set()).add(r["part"])
assert all(v == {"en", "es"} for v in frames.values()), "every frame needs an English and a Spanish item"
correct_sentences = [r["correct"] for r in items.values()]
assert len(correct_sentences) == len(set(correct_sentences)), "duplicate correct sentences"

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biagram_testset_v2.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"Wrote {len(rows)} pairs, {len(items)} items -> {out}")
