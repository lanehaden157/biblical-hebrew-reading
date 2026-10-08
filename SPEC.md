# Biblical Hebrew Reading Curriculum: Build Spec (v1)

Audience: the builder (Claude Code) and Lane. Scope: zero-to-reading for Biblical Hebrew **narrative prose**, recognition only, ending with **unaided** reading of Exodus 3 and Exodus 14.

## 0. Conventions and ground rules

- **No Hebrew script appears in this file.** Every form is named by transliteration and, where useful, a verse reference or Strong's number. These are *lookup labels, not display strings*. If a label here disagrees with the corpus, the corpus wins and the builder should log the mismatch.
- Transliteration follows Lane's scheme. Where the scheme is silent (vowels, spirantized b/k/p), I write a/e/i/o/u, keep `b` and `p` unchanged, and write spirant kaf as `kh` as Lane did in "halakh". Resolved: see section 7.
- `MEASURE:` marks a statistic the builder must compute from the tagged corpus. All MEASURE items are collected in Appendix A.
- Evidence labels: **[Strong]** replicated or meta-analytic; **[Moderate]** several studies or consistent expert practice; **[Weak]** few studies or indirect; **[Opinion]** my design judgment or extrapolation.
- Sources are listed in Appendix C. Items marked *(from memory)* were not re-verified in this research pass.

### 0.1 Corpus definition (changed from the original brief)

Lane's revised instruction: frequency is computed over **narrative prose only**, with proper nouns and other non-vocabulary handled separately.

**Narrative corpus (config file, editable):** Genesis, Exodus, Numbers, Joshua, Judges, Ruth, 1–2 Samuel, 1–2 Kings, Jonah. *(Resolved Q2: late books dropped.)*

**Excluded from the corpus:**
- All Aramaic tokens (Dan 2:4b–7:28; Ezra 4:8–6:18; 7:12–26), identified by the language field of the morphology tag, not by hand-typed ranges.
- Embedded poems: Gen 49:2–27; Exod 15:1–18; Num 23–24 oracles; Judg 5; 1 Sam 2:1–10; 2 Sam 22; 2 Sam 23:1–7; Jonah 2:3–10 (Hebrew versification). MEASURE: confirm exact verse bounds against the corpus and list any others the builder finds.
- [Opinion] Leviticus and Deuteronomy are prose but legal/sermonic, so I left them out. Long legal blocks inside Exodus and Numbers stay in for simplicity. Confirmed (Q2).

**Not ranked as vocabulary (handled separately):**
| Class | Handling |
|---|---|
| Proper nouns (people, places, gentilics, the divine name) | "Names" track: recognize as a name plus who/what; never counted in lemma ranks |
| Inseparable prefixes (conjunction w-, article ha-, prepositions b-/l-/k-, mi(n)- when prefixed, relative she-, interrogative ha-) | Morpheme items in the grammar track |
| Pronominal suffixes, noun/verb endings | Morpheme items |
| Ketiv/qere pairs | Display and count the qere |
| Paragraph markers and other non-word tokens | Dropped |

**Lemma key:** the corpus's own lemma ID (augmented Strong's, which separates homographs). Never merge or split lemmas by hand.

**Coverage is always reported two ways:** (a) lemma coverage of ranked vocabulary tokens, (b) full-token coverage including names and prefixes. Show (a) as the headline and (b) on tap.

**Lane's earlier measurements** (about 600 lemmas ≈ 80% of tokens; conjugation and binyan shares; strong Qal ≈ 4% of verb tokens) are treated as Lane's inputs on an unspecified corpus. MEASURE: recompute all of them on the narrative corpus before fixing rank cut-offs.

---

## 1. Summary of findings

### 1.1 Reading research: what transfers to 5–10 minutes a day

1. **Vocabulary coverage drives comprehension, with no magic threshold.** Schmitt, Jiang & Grabe (2011; 661 learners) found a roughly linear relation between percent of words known and comprehension, and recommend 98% as the target for unassisted reading. Hu & Nation (2000) found nobody comprehended adequately at 80% coverage and only a minority at 90–95%. **[Strong for modern languages; extrapolated to Biblical Hebrew.]**
   - Consequence: 600 lemmas at about 80% is *not* an unaided-reading vocabulary. "Unaided Exodus 3 and 14" is reachable only because it is two specific chapters whose remaining vocabulary can be taught directly (Unit 11). Unaided reading of arbitrary narrative is a multi-year goal.
2. **Glossed reading beats unglossed reading for beginners.** A meta-analysis of 42 studies found glossed reading produced about 45% word learning on immediate tests versus about 27% unglossed, with first-language glosses better than second-language ones (Yanagisawa, Webb & Uchihara 2020). A separate meta-analysis found the first-language advantage is largest for beginners. **[Strong]** Consequence: tap-for-English-gloss is the right help, and glossing lets real text start long before 98% coverage.
3. **Reading alone teaches vocabulary slowly.** Incidental learning from reading runs around 15–17% of unknown words met (Webb, Uchihara & Yanagisawa 2023). **[Strong]** Consequence: vocabulary must be taught by deliberate spaced retrieval; reading consolidates and builds fluency.
4. **Extensive reading works, modestly.** Nakanishi (2015; 34 studies) found d ≈ 0.46 against controls; a later bias-adjusted estimate is about 0.37 (Hamada 2020). Effects were larger for adults and for programs lasting a year. **[Moderate]** These programs involve hours per week, so the transfer to 2–3 minutes a day is **[Opinion]**: keep reading in every session, re-read passages, and expect the benefit to come mainly late in the course.
5. **Retrieval practice and spacing are the two best-supported study techniques** (Dunlosky et al. 2013). **[Strong]** This supports FSRS plus Hebrew→English recall; nothing to change.
6. **Audio:** reading-while-listening consistently helps vocabulary learning; results for comprehension are mixed. **[Moderate, modern languages only]** Consequence: audio is a cheap support on card reveal and in the reader, not a separate skill to drill.
7. **Short daily sessions:** I found no direct study of 5–10 minute sessions for an ancient language. The fit rests on the spacing literature plus arithmetic about review load (section 1.6). **[Opinion]**

### 1.2 How the textbooks sequence material

| Curriculum | Sequence | Weak verbs | Reading |
|---|---|---|---|
| Pratico & Van Pelt | 36 chapters; nouns, prepositions, pronouns, suffixes, construct first; verbs start at ch. 12; Qal perfect strong (13) then weak (14); imperfect strong (15) then weak (16); derived stems each split strong/weak (24–35) | Paired with each strong chapter; "diagnostics" instead of full paradigms | Late; separate graded reader |
| Futato | 40 short chapters; Qal strong verb early; 400-word vocabulary | Hollow verbs ch. 25; weak chapters paired with each derived stem | Short biblical phrases per chapter; Gen 1–2 at the end in one course plan |
| Ross | 54 lessons: 1–6 sounds, 7–40 forms, 41–54 Genesis readings | Strong first, then weak in a second pass | Last quarter of the book |
| Kelley | 31 lessons: 1–10 non-verbal, 11–20 strong verb, 22–31 ten weak classes | All at the end | Exercises from biblical text throughout |
| Fuller & Choi | Phonological rules first; strong verb in all stems; then weak classes | After all strong stems | Late |
| Garrett & DeRouchie | Verb overview in ch. 6; first verbs met are weak; weak roots introduced through principal parts (3ms forms) early; full weak paradigms in ch. 27–30 | Early, by principal parts | Biblical text from lesson 8; discourse-aware |
| Cook & Holmstedt | Reduced grammar load, SLA-informed, illustrated readings | Integrated | Genesis episodes are the spine |
| Kittel, Hoffer & Wright | 55 lessons, each built on a verse; lesson 1 is the wayyiqtol | Met as they occur | From lesson 1 |
| Biblical Language Center (Buth) | Communicative, picture-based, then texts | Absorbed in use | Jonah in year 1, Ruth next |
| Reader's editions | Not courses. Zondervan glosses words occurring 100 times or fewer; the BHS Reader's Edition glosses under 70 and parses every weak verb form except the very common ones | n/a | Assume about a year of grammar plus roughly 500 words |

**Where they agree:** teach by frequency; Qal before derived stems; high-frequency vocabulary lists; derived stems recognized by a few signals.

**Where they differ:** (a) how long verbs are delayed (a third of the book in Pratico & Van Pelt; lesson 1 in Kittel); (b) strong-before-weak versus weak-early; (c) paradigm memorization versus diagnostics; (d) when real text begins.

**What fits this learner [Opinion, informed by the comparison]:** verbs from the first weeks (Kittel, Futato); weak verbs early via a few very common forms (Garrett & DeRouchie); diagnostics rather than paradigms (Pratico & Van Pelt); help modeled on the BHS Reader's Edition (gloss the rare, parse the weak); Jonah then Ruth as first connected texts (Buth). No controlled study compares these sequences, so this is expert practice, **[Weak]** as evidence.

### 1.3 Verb system for recognition

- **Weak verbs first, as whole words.** With strong Qal at about 4% of verb tokens (Lane's measurement), strong-first sequencing spends the early months on forms the learner rarely meets. Garrett & DeRouchie's weak-early approach has precedent, and a reviewer's complaint about it (too much explanation at once) argues for teaching *forms* before *rules*. **[Opinion]**
- **Three layers, in this order:** (1) the most frequent inflected forms learned as vocabulary (wayyo'mer, Gen 1:3, is learned as "and he said" before any analysis); (2) markers that generalize (prefix letters, endings, stem signals); (3) root-recovery rules for the "missing letter" classes. This mirrors the item-then-pattern route that comprehension-first grammar teaching favors *(Norris & Ortega 2000; VanPatten's processing instruction; from memory)*. **[Moderate for the general principle; Opinion for this application]**
- **Paradigm slots are a reference, not a drill.** Recognition needs "what does this ending tell me", not "recite the ninth slot". Keep tables browsable.
- **How many parsing items:** my estimate is about 45 marker/rule items plus about 330 attested-form items. This is a judgment, to be validated by MEASURE M7 (coverage of verb tokens by the top N inflected forms).

### 1.4 When to start connected text

Start in Unit 1 with real two-to-six-word phrases under full help, single verses from Unit 3, and continuous chapters from Unit 6. Glossing removes the coverage barrier (1.1 item 2). Fade help in the order: translation hidden → known-word glosses hidden → parses on tap only → rare-word glosses only → nothing. **[Opinion built on Strong glossing evidence]**

### 1.5 Decoding and audio

Lane already decodes pointed text. Unit 0 is therefore a one-week calibration, not an alphabet course. Automatic word recognition matters for reading fluency *(LaBerge & Samuels; Koda; from memory)*, and the cheapest way to build it is volume, so decoding practice is folded into every card and reading. Audio plays on reveal and optionally alongside passages. No audio-only items. **[Moderate / Opinion]**

### 1.6 Timeline (honest version)

Inputs from Lane: 5–10 minutes a day (soft ceiling). Assumptions of mine: 8 seconds per review on average; each new item per day costs about 7 reviews per day at steady state; a new item costs about 25 seconds on its first day; reading takes about 30% of the session. MEASURE M12 replaces all of these with Lane's real numbers after 30 days.

Arithmetic: per new item per day, 7 × 8 s + 25 s = 81 s.

| Daily time | Reading share | Card time | New items/day | Days for 1,315 items + 21 days (Units 0 and 12) | Calendar at 6 days/week |
|---|---|---|---|---|---|
| 5 min | 90 s | 210 s | 2.6 | 527 | about 20 months |
| 8 min | 150 s | 330 s | 4.1 | 342 | about 13 months |
| 10 min | 180 s | 420 s | 5.2 | 274 | about 10.5 months |

**Verdict:** 12 months is realistic at a true 8–10 minutes on most days. At a strict 5 minutes it is roughly 18–20 months. What would have to give to hit 12 months at 5 minutes: drop the reading share (not recommended), or cut the frequency core from 750 to about 450 lemmas and rely on a larger Exodus top-up, which weakens general reading ability.

---

## 2. Learning model

**Core theory in one paragraph.** Reading is fast recognition of words and word-parts, held together by a small amount of grammar. So the course (1) builds a recognition vocabulary in frequency order by spaced retrieval, (2) teaches the grammar that narrative actually uses, starting with the most common real forms and only then the patterns behind them, and (3) puts both to work every day on real text with help that is withdrawn as the data show it is no longer needed.

**Two parallel tracks, deliberately decoupled:**
- **Vocabulary queue:** continuous, strict frequency order on the narrative corpus. It never waits for a grammar unit and is never reordered by reading choices. (Fixed decision preserved.)
- **Grammar track:** the units below. Each adds concepts, morpheme items, marker items and whole-form verb items.

Unit "vocabulary ranges" are where the queue is *expected* to be, not gates.

**What is drilled, read, explained:**
| Mode | Content | Share of session |
|---|---|---|
| Drilled (FSRS) | lemmas; morphemes; whole verb forms; marker discriminations; names | about 70% |
| Read | micro-readings, then passages, with logged help | about 30% |
| Explained | one-screen lessons (under 150 words, 3–5 corpus examples), shown once when a concept unlocks, always re-openable | under 1 minute, only on unlock days |

**Trust rules (the build must enforce these):**
1. Hebrew text, lemma and parse come only from the corpus. No model-written or hand-typed Hebrew anywhere, including lessons; lessons reference tokens by ID.
2. Parses are cross-checked against an independent analysis (ETCBC BHSA; note MACULA Hebrew reuses OSHB morphology, so it is *not* independent for parses). Tokens where the two disagree are quarantined from parse items and listed for review.
3. Glosses are seeded from licensed lexical data (STEPBible TBESH brief lexicon, based on abridged BDB; token-level glosses from MACULA or STEPBible TAHOT) and then curated. Each gloss stores its source and a "reviewed by Lane" flag. Unreviewed glosses are visibly marked.
4. Transliteration and audio are generated by one tested function from the corpus text, never typed.
5. Any surface form with more than one attested parse is shown in its verse and graded against that token's tag; isolated presentation is allowed only for unambiguous forms (MEASURE M9).
6. Every item has a "report a problem" tap that quarantines it.

---

## 3. Curriculum outline

Item budget: 750 ranked lemmas, 60 morpheme items, 45 marker/rule items, 300 whole-form verb items, 50 names, plus an Exodus top-up assumed at up to 110 items (MEASURE M10). Total about 1,315. Day estimates assume 4 new items per day.

**"Ready to move on" is advisory.** The app suggests the next unit; it never blocks. Shared definitions:
- *Known item:* FSRS state = review, stability ≥ 21 days, last rating not "Again".
- *Parse accuracy:* first-attempt, all requested facets correct, over the last 40 parse reviews tagged to the unit.
- *Retention:* share of non-"Again" ratings on review-state cards over the trailing 14 days.
- *Help rate:* gloss or parse taps per 100 words on a passage not seen before.
- *Spot check:* 5 random tokens from the passage just read; pick the contextual gloss from 4 options (distractors same part of speech, auto-generated from data).

### Unit 0. Calibration (7 days, 0 scheduled items)
- **Goal:** read any pointed word aloud at first sight; know the app's transliteration and help controls.
- **Prerequisites:** none.
- **Lessons:** silent versus vocal sheva; dagesh (doubling versus hard b/k/p); the two readings of qamats; furtive patakh; vowel letters; maqqef; final forms; look-alike letters; how the divine name is displayed and voiced (Q3).
- **Vocabulary / verbs:** none scheduled; queue opens on day 3 at 2 new per day.
- **Reading:** 40 single words drawn from Gen 1 and Jonah 1, with audio.
- **Mastery:** 30-item check (hear or see a word, choose its transliteration from 4): ≥ 90% correct, median response under 4 s. Passing on day 1 skips the unit.
- **Change at exit:** transliteration switches to tap-to-show (see section 7, R1).

### Unit 1. The glue (18 days, 72 items)
- **Goal:** split any word into prefix(es) + core; read verbless clauses.
- **Prerequisites:** Unit 0.
- **Lessons:** conjunction w-; article ha- (and its doubling); b-, l-, k-, mi(n)-; the object marker 'et (H853); 'asher; "X is Y" clauses with no verb; how wayyo'mer and wayhi are learned as wholes for now.
- **Vocabulary:** ranks 1–50. **Morphemes:** 14. **Whole verb forms (8):** MEASURE M6, the 8 most frequent inflected verb forms in the corpus. Expected to include wayyo'mer (Gen 1:3), wayhi (Gen 1:3), le'mor (Exod 14:1).
- **Reading:** micro-readings. MEASURE M8a: 2–6 word phrases (split at major disjunctive accents) in which every lemma is rank ≤ 50 or a name. Help: full interlinear (gloss under every word, prefixes color-segmented, translation on reveal).
- **Mastery:** morpheme items ≥ 85% over last 40; prefix-segmentation drill ≥ 90% over last 20.

### Unit 2. Nouns and their attachments (29 days, 116 items)
- **Goal:** read a noun phrase: number, gender, "of" chains, possessors.
- **Prerequisites:** Unit 1.
- **Lessons:** endings -im, -ot, -ah, -ayim; construct chains (recognition cues: shortened vowels, -ey, -at); adjectives follow nouns; independent pronouns; pronominal suffixes on nouns and on prepositions (lo, li, lekha, 'elaw, `immo and so on); demonstratives.
- **Vocabulary:** ranks 51–120. **Morphemes:** 30. **Whole verb forms:** next 6 from M6. **Names:** top 10 by frequency.
- **Reading:** MEASURE M8b: phrases and short clauses, lemmas rank ≤ 120. Help: glosses shown only for words not yet "known"; suffixes highlighted.
- **Mastery:** suffix items ≥ 80% over last 40; retention ≥ 85%.

### Unit 3. The story tense: wayyiqtol (33 days, 133 items)
- **Goal:** recognize a wayyiqtol as "and [someone] did X", and name person/gender/number from the prefix and ending.
- **Prerequisites:** Units 1–2.
- **Lessons:** wa- + doubled prefix letter; prefix letters y/t/'/n and what each means; 3ms, 3fs, 3mp as the narrative workhorses; first root-finding heuristic (strip wa- and prefix, look for three consonants; if only two remain, a letter has dropped, to be explained in Unit 7).
- **Vocabulary:** ranks 121–190. **Markers:** 8. **Whole verb forms (55):** MEASURE M6 filtered to wayyiqtol. Expected to include wayyar' (Gen 1:4), wayya`as (Gen 1:7), wayyiqra' (Exod 3:4), wayyitten (Gen 1:17), wayyelekh (Gen 12:4), wayyabo' (Exod 3:1), wayyiqqakh (Gen 22:6), wayyaqom (Jonah 1:3), wayyered (Jonah 1:3), wayyashob (Gen 22:19), wayyamot (Gen 5:5), wayyishma` (Gen 21:17), wayyishlakh (Gen 22:10), waydabber (Exod 14:1). These are mostly weak verbs, by design.
- **Reading:** single verses. MEASURE M8c: verses whose main verbs are all wayyiqtol or verbless, lemmas ≥ 90% known. Help: glosses for unknown lemmas; parse on tap.
- **Parsing asked:** conjugation + person/gender/number only (root and stem facets not yet requested).
- **Mastery:** parse accuracy ≥ 80%; whole-form items ≥ 85% over last 40.

### Unit 4. Qatal (33 days, 133 items)
- **Goal:** recognize suffix-conjugation forms and tell them from wayyiqtol; understand weqatal as "and he will/would".
- **Prerequisites:** Unit 3.
- **Lessons:** endings -ti, -ta, -t, -ah, -nu, -tem, -u, and bare 3ms; why speech and background use qatal; lo' + qatal; weqatal; the short two-consonant qatals (ba', qam, shab, met); final-he verbs (`asah, `asita Gen 3:14, `asu); natatti (Gen 1:29).
- **Vocabulary:** ranks 191–260. **Markers:** 8. **Whole verb forms:** 45 (M6, qatal and weqatal). **Names:** next 10.
- **Reading:** MEASURE M8c with qatal allowed; begin 2–3 verse snippets.
- **Parsing asked:** conjugation + PGN.
- **Mastery:** parse accuracy ≥ 80%; qatal-versus-wayyiqtol discrimination ≥ 90% over last 20.

### Unit 5. Yiqtol and commands (31 days, 123 items)
- **Goal:** read direct speech: futures, wishes, commands, prohibitions.
- **Prerequisites:** Unit 4.
- **Lessons:** yiqtol as wayyiqtol without wa-; -u and -i endings; imperative as "yiqtol minus the prefix" (qum, lekh: Jonah 1:2); jussive and cohortative (-ah) as recognition-only shades; lo' versus 'al; na'.
- **Vocabulary:** ranks 261–330. **Markers:** 8. **Whole verb forms:** 45 (yiqtol, imperative, jussive, cohortative). Include 'ehyeh (Exod 3:14) and shal (Exod 3:5) only if M6 ranks them; otherwise they arrive in Unit 11.
- **Reading:** MEASURE M8d: dialogue-heavy snippets (3–5 verses), lemmas ≥ 90% known.
- **Parsing asked:** conjugation + PGN.
- **Mastery:** parse accuracy ≥ 80% across Units 3–5 forms mixed.

### Unit 6. Participles and infinitives; first chapters (30 days, 120 items)
- **Goal:** read a continuous chapter with reader's-edition help.
- **Prerequisites:** Unit 5.
- **Lessons:** participle as "-ing / one who" (endings as on nouns; o-e vowel pattern in Qal); hinneh + participle; infinitive construct with l- ("to do": la`asot, Gen 2:3) and with b-/k- + suffix ("when he..."); wayhi + time phrase; infinitive absolute as recognition-only emphasis.
- **Vocabulary:** ranks 331–400. **Markers:** 5. **Whole verb forms:** 35. **Names:** next 10 (include Jonah's cast).
- **Reading:** Gen 12:1–9 first (decided 2026-10-08: 90.7% coverage at rank 400 vs Jonah 1 at 80.5%), then Jonah 1; 2:1–2, 11; 3; 4 (Hebrew versification; the psalm is skipped). MEASURE M11: coverage of each chapter at entry. Help level "Reader": glosses always visible for lemmas beyond rank 750 or not yet introduced; tap for anything else; parses on tap; audio optional. Each chapter is read twice, at least 3 days apart.
- **Parsing asked:** conjugation + PGN + root (choose from 4).
- **Mastery:** on second reading of Jonah 3, help rate ≤ 15 per 100 words and spot check ≥ 4/5.

### Unit 7. Recovering the root (30 days, 118 items)
- **Goal:** name the root of a weak form met for the first time.
- **Prerequisites:** Unit 6. By now about 180 weak forms are known as wholes; the rules explain what the learner has already seen.
- **Lessons (one rule each, with the already-known forms as examples):**
  1. Doubled first visible consonant after the prefix → a nun was absorbed (wayyitten, wayyiqqakh; laqakh behaves this way too).
  2. Prefix vowel e, only two consonants → first-yod/waw verb (wayyered, wayyesheb; halakh behaves this way: wayyelekh).
  3. Two consonants with a long vowel between or before → hollow verb (wayyaqom, wayyabo', qam).
  4. Form ends in a vowel or is cut short → final-he verb (wayya`as, wayyar', wayhi; -ita, -ot endings).
  5. Prefix vowel o with alef → the small 'amar/'akhal group.
  6. Doubled second consonant with only two root letters visible → geminate (recognition only).
  7. Two rules at once (wayyet, Exod 14:21; wayyakh) → learn as wholes.
  8. Gutturals shift vowels but never remove letters.
- **Vocabulary:** ranks 401–480. **Markers/rules:** 8. **Whole verb forms:** 30.
- **Reading:** Ruth 1–2. Help level "Reader".
- **Parsing asked:** root + conjugation + PGN (stem assumed Qal unless flagged).
- **Mastery:** root identification on *unseen* weak forms (forms never shown as items; MEASURE M9b supplies the pool) ≥ 75% over last 40.

### Unit 8. Piel and Hiphil (36 days, 145 items)
- **Goal:** spot the two most common derived stems and adjust the meaning.
- **Prerequisites:** Unit 7.
- **Lessons:** Piel signal (doubled middle consonant; sheva under the prefix; mem- participle); Hiphil signal (h- prefix in qatal/imperative/infinitive; a-i vowels under yiqtol prefix; "cause to" meaning; mem- participle); common Hiphils that look nothing like their Qal (wayyagged; hotsi'; hebi'; wayyosha`, Exod 14:30). Lemma glosses for these verbs are stem-specific (one card per lemma+stem where the meaning differs: MEASURE M5).
- **Vocabulary:** ranks 481–570. **Markers:** 5. **Whole verb forms:** 40. **Names:** next 10.
- **Reading:** Ruth 3–4; then Genesis selections chosen by MEASURE M11 from candidates Gen 22:1–19, Gen 1:1–2:3, Gen 12:1–9, Gen 37.
- **Parsing asked:** all four facets (root, stem, conjugation, PGN).
- **Mastery:** stem discrimination Qal/Piel/Hiphil ≥ 85% over last 40; full-parse accuracy ≥ 70%.

### Unit 9. Niphal, Hitpael, and the rare stems (31 days, 123 items)
- **Goal:** recognize passive/reflexive forms; not be thrown by Pual and Hophal.
- **Prerequisites:** Unit 8.
- **Lessons:** Niphal (n- prefix in qatal and participle; doubled first root letter in yiqtol: wayyera', Exod 3:2; yillakhem, Exod 14:14); Hitpael (hit-/yit- prefix: hityatsvu, Exod 14:13); Pual and Hophal as "u-class vowel = passive" (wayyuggad, Exod 14:5). Pual, Hophal and rarer stems get one recognition lesson and no scheduled items beyond forms that M6 ranks.
- **Vocabulary:** ranks 571–660. **Markers:** 3. **Whole verb forms:** 30.
- **Reading:** Genesis selections continued. Help level "Light": only lemmas outside the learner's introduced set are pre-glossed.
- **Mastery:** five-stem discrimination ≥ 80% over last 40; help rate on an unseen Genesis passage ≤ 10 per 100 words.

### Unit 10. Verbs with objects attached; clause connectors (31 days, 122 items)
- **Goal:** read long sentences: verb + object suffix, subordinate clauses, numbers.
- **Prerequisites:** Unit 9.
- **Lessons:** object suffixes on verbs (-ni, -kha, -hu/-o, -ha, -nu, -m); ki, 'im, pen, lema`an, `ad, ka'asher as clause signals; directional -ah; question ha-; numbers as a set; oath and "behold" formulas.
- **Vocabulary:** ranks 661–750. **Morphemes:** 16. **Whole verb forms:** 6. **Names:** next 10 (include the Exodus cast and places).
- **Reading:** Exod 1–2 at help level "Light" (same vocabulary field as the target chapters).
- **Mastery:** verb-suffix items ≥ 80% over last 40; help rate on Exod 2 second reading ≤ 8 per 100 words.

### Unit 11. Exodus approach (28 days, up to 110 items)
- **Goal:** know every word and verb form in Exod 3 and Exod 14 before reading them cold.
- **Prerequisites:** Unit 10; frequency queue at rank ≥ 750 or paused by choice.
- **Content:** MEASURE M10a: every lemma in Exod 3 and 14 not yet introduced (budget 80), taught in order of corpus frequency. MEASURE M10b: every inflected verb form in the two chapters whose parse the learner's history does not yet cover (budget 30). Decided 2026-10-08: M10b found 128 forms outside the top 300; teach as whole forms only those the Unit 3–10 rules do not explain, drilled in their verse. Names: any remaining.
- **Note:** this is the one place vocabulary is passage-targeted. It is a top-up after the frequency core, not an ordering principle. If M10a exceeds 120, extend the unit; do not shrink the core.
- **Reading:** none of Exod 3 or 14 yet. Re-read Exod 1–2 and one Genesis passage with help off.
- **Mastery:** ≥ 95% of the lemmas and forms occurring in Exod 3 and 14 are "known"; retention ≥ 88%.

### Unit 12. Milestone (14 days, 0 new items)
- **Goal:** read Exod 3, then Exod 14, with all help off, and understand them.
- **Procedure:** cold read in 5–8 verse sittings. Help is available but hidden behind a deliberate "I need help" action that is logged. After each sitting: reveal a public-domain translation (Q5) and run the spot check.
- **Pass:** help rate ≤ 2 per 100 words and spot check ≥ 90% across each chapter. Each lookup creates or resets an item; the chapter can be re-attempted after 7 days.

**Totals:** 351 practice days at 4 new items per day.

---

## 4. Daily session design

**Default "Today" (target 8 minutes, hard stop offered at 10):**
| Block | Time | Content |
|---|---|---|
| 1. Review | about 4 min | Due FSRS items, all types interleaved. Time-boxed: if the box ends, remaining reviews roll to tomorrow without any backlog counter shown. |
| 2. New | about 1.5 min | Up to N new items: vocabulary queue first, then the current unit's grammar items, in a 3:2 ratio when both are available. A concept lesson appears only on the day its first item unlocks. |
| 3. Read | about 2.5 min | The next micro-reading or the next 3–6 verses of the current passage. Ends with one spot-check item at most twice a week. |
| 4. Done | 10 s | One progress line (section 5) and three buttons: finish, more reading, more drill. |

**Adaptation rules:**
- N starts at 4. If block 1 overruns its box on 3 of the last 5 sessions, N drops by 1 (minimum 0). If block 1 finishes under 3 minutes on 5 sessions running and retention ≥ 88%, N rises by 1 (maximum 8).
- After a gap of any length: no penalty, no message about the gap, N = 0 until the review box stops overrunning. FSRS handles the rescheduling.
- Reading share grows with level: 20% in Units 1–2, 30% in Units 3–7, 40% from Unit 8.
- A "5-minute day" toggle gives review + one short reading, no new items.

**Freedom without derailment:**
- **Library:** every corpus chapter is openable at any time at any help level. Free reading never adds items automatically. Tapping a word offers "pin": pinned lemmas join a separate small queue (maximum 2 per day, counted inside N) so the frequency order of the main queue is untouched.
- **Lessons:** all browsable from day 1. Opening a later lesson unlocks nothing.
- **Jump to unit:** allowed. The app states which earlier marker items are unseen and offers to add them; it does not refuse.
- **Extra drill:** "practice" mode on any item type or unit. Practice results are logged for accuracy statistics but do not write to FSRS state, so cramming cannot distort the schedule.
- **Extra reading:** continue the current passage, or "something easy" (a passage already read, or one with the highest current coverage: MEASURE M11).

---

## 5. Progress and milestones

**Always visible (no streaks, no calendars of missed days, no "days behind"):**
1. Exodus 3 and Exodus 14 lemma coverage (known tokens / ranked tokens), with full-token coverage on tap.
2. Narrative-corpus coverage for the learner's known set.
3. Lemmas known / introduced.
4. Parse accuracy (last 40) and stem discrimination (from Unit 8).
5. Help rate on the most recent unseen passage.
6. Verses read (cumulative; a count that only goes up).
7. A forecast range for the milestone, computed from the trailing 30 days of actual pace, shown as "at your recent pace: X–Y" and never as a deadline.

**Targets by month (8 min/day plan, which runs nearer 13 months than 12, so each row may land up to a month late; values are checkpoints, not obligations):**
| Month | Unit reached | Lemmas introduced | Corpus coverage | Exod 3 / 14 coverage | Parse accuracy | Help rate |
|---|---|---|---|---|---|---|
| 3 | end of 3 | about 190 | MEASURE M2 at rank 190 | MEASURE M3 at rank 190 | ≥ 80% (conj + PGN) | n/a |
| 6 | end of 6 | about 400 | MEASURE M2 at rank 400 | MEASURE M3 at rank 400 | ≥ 80% (conj + PGN + root) | ≤ 15 |
| 9 | late 9 | about 640 | MEASURE M2 at rank 640 | MEASURE M3 at rank 640 | ≥ 70% full parse | ≤ 10 |
| 12 | 12 | 750 + top-up | MEASURE M2 at rank 750 | ≥ 95% known | ≥ 75% full parse | ≤ 2 on Exod 3 and 14 |

Retention target throughout: 85–90%.

---

## 6. Item types

| # | Type | Front → back | Scheduled? | Rationale |
|---|---|---|---|---|
| 1 | Lemma recognition | Lemma (dictionary form) → gloss, one example verse, audio | FSRS | Core vocabulary; retrieval + spacing |
| 2 | Morpheme | A real word with one segment highlighted → what that segment means | FSRS | Prefixes and suffixes are a large share of what is on the page |
| 3 | Whole verb form | Inflected form in its verse → contextual gloss + parse | FSRS | Gets the commonest weak forms in early, as words |
| 4 | Reverse parse | Form in its verse → choose root (from 4), stem, conjugation, PGN with chips; only the facets taught so far | FSRS (all facets right = Good; any wrong = Again) | The fixed verb-teaching decision; chips keep it fast on a phone and auto-gradable |
| 5 | Marker discrimination | Two or three forms → which is the Hiphil / the qatal / the plural? | FSRS on the contrast, rotating exemplars | Teaches the signal, not the exemplar |
| 6 | Root identification on unseen forms | Never-shown weak form → root (from 4) | Not FSRS; sampled pool | The only honest test of whether the rules generalize |
| 7 | Micro-reading | Phrase or verse → self-check against revealed gloss line | Not FSRS; each shown twice, 3+ days apart | Daily connected text from week 2 |
| 8 | Passage reader | Continuous text with help levels and tap logging | Not FSRS | The actual goal behavior; produces help-rate data |
| 9 | Spot check | Token from a passage just read → contextual gloss from 4 | Not FSRS | Objective comprehension signal with no hand-authored questions |
| 10 | Name recognition | Proper noun → "name: who/where" | FSRS, low priority | Names are frequent; unknown names stall reading |
| 11 | Decoding check | Word → transliteration from 4 / audio match | Unit 0 only, plus a 10-item speed probe every 60 days | Confirms decoding is not the bottleneck |

**Drop or demote from the current design:**
- **Strong-verb Qal paradigm gym as a core activity.** Strong Qal is about 4% of verb tokens (Lane's figure). Replace with types 3–6 on attested forms; keep paradigm tables as reference.
- **Any paradigm-slot recitation or form production.** Recognition goal only.
- **Typed answers.** Slow on a phone and they test spelling in English.
- **Audio-only cards.** Listening comprehension is not a goal.
- **Parsing forms out of context when the form is ambiguous** (for example ba', which can be qatal or participle). Show in verse or do not show.
- **Any gloss or example text generated by a language model without a source field.**

---

## 7. Open questions and risks

### Resolved decisions (2026-10-07)

Original wording of R1–R3 and Q1–Q6 is replaced by the outcomes below. `BUILD_PLAN.md` carries the same table.

- **R1. Transliteration visibility.** Accepted: every form has a transliteration, shown on tap after Unit 0; Settings can keep it always on.
- **R2. Audio.** Not in v1.
- **R3. Frequency vs "unaided".** Exodus top-up (Unit 11) accepted.
- **Q1. Transliteration details.** b/v, k/kh, p/f by dagesh; doubled consonants written double (dagesh forte); vocal shva written `e`; qamats qatan `o`. Root displays use Hebrew letters (lookup by token id). Added 2026-10-08: vav `v`, het `ch`, tsade `ts`, ayin `` ` ``; alef `'` only when consonantal and not word-initial; final he written `h`; plain a/e/i/o/u (hatefs a/e/o); acute accent on the stressed vowel only when stress is not final (mélekh); no prefix hyphens (laYHWH); maqqef = hyphen. Dropped-dagesh shva after vav-consecutive is always vocal (vayehi, vayevárekh); after ha- only before a soft b/k/p. Furtive patach takes the stress mark (rúach). Final he is `h` whether silent or mappiq.
- **Q2. Corpus boundary.** Gen, Exod, Num, Josh, Judg, Ruth, 1-2 Sam, 1-2 Kgs, Jonah. Prose only, embedded poems removed. No Esther, Ezra, Nehemiah, Daniel, Chronicles; no Lev/Deut. This supersedes the book list in 0.1.
- **Q3. Divine name.** Pointed text shown as printed; transliteration `YHWH`; gloss "YHWH (the LORD)".
- **Q4. Gloss source.** Seeded from STEPBible TBESH, curated per occurrence against BDB, each gloss carries a source and a `reviewed` flag. Changed 2026-10-08: no per-unit review batch (Lane cannot check Hebrew against BDB); Lane reports problems while studying and fixed glosses become reviewed. The app should mark unreviewed glosses subtly, since nearly all will be.
- **Q5. Reveal translation.** Gloss line plus WEB translation (needs a verified Hebrew-to-English verse map).
- **Q6. Verb cards.** One card per lemma+stem when the stem has at least 20 tokens (M5) and a distinct meaning.
- **Sync.** Dropped. localStorage plus export/import only.
- **Phase 2 (2026-10-08, from MEASURES.md).** Core stays 750 lemmas. Unit 11 forms: rule-opaque ones only (see Unit 11). Gen 12:1–9 opens Unit 6. Poems 2 Sam 1:19–27 and 2 Kgs 19:21–28 removed; short couplets kept. Hishtachaveh (H7812): one lemma+stem card "bow down", stem facet not asked (OSHB and BHSA disagree).

### Where this plan is most likely to fail at 5–10 minutes a day
1. **Review load crowds out reading.** Mitigation: time-boxed review, automatic throttling of new items, protected reading block.
2. **Months 4–7 plateau:** vocabulary is growing but real chapters still need much help. Mitigation: micro-readings chosen for ≥ 90% coverage so some real text always feels readable; coverage numbers that visibly rise.
3. **Whole-form cards become rote** (recognizing the card, not the form). Mitigation: type 6 unseen-form pool; marker items rotate exemplars.
4. **Data errors surface late and break trust again.** Mitigation: the six trust rules in section 2; cross-source disagreement list reviewed before launch; per-item report button.
5. **Parsing takes too long per card.** If median parse time exceeds 15 s, reduce facets requested per card to two, rotating.
6. **The timeline assumptions are mine, not measured.** M12 replaces them after 30 days; the forecast should then be trusted over section 1.6.
7. **Top-up larger than assumed.** If M10a is well over 80 lemmas, Unit 11 lengthens proportionally (about 1 day per 4 items).

---

## Appendix A. MEASURE list (all on the narrative corpus of 0.1 unless stated)

- **M1.** Ranked lemma list: lemma ID, token count, rank, after removing the excluded classes. Also the counts removed per class.
- **M2.** Cumulative token coverage (both definitions) at ranks 50, 120, 190, 260, 330, 400, 480, 570, 660, 750, 1000, 1500, 2000.
- **M3.** Coverage of Exod 3 and of Exod 14 at the same ranks; total tokens and distinct lemmas in each chapter.
- **M4.** Recompute Lane's verb statistics: share of verb tokens by conjugation, by stem, and the share that are Qal strong.
- **M5.** For each verb lemma, token counts by stem; list lemma+stem pairs with ≥ 20 tokens.
- **M6.** Inflected verb forms (surface form + full parse) ranked by token count; top 400 with one example reference each. Mark which belong to wayyiqtol, qatal/weqatal, yiqtol/volitives, participles, infinitives.
- **M7.** Share of all verb tokens covered by the top 100, 200, 300, 400 forms of M6.
- **M8a–d.** Micro-reading pools as specified in Units 1, 2, 3–4, 5: list of references, word counts, coverage at the stated rank.
- **M9.** (a) Surface forms with more than one attested parse. (b) Weak-verb forms outside the M6 top 400, grouped by weak class, as the unseen-form pool.
- **M10.** (a) Lemmas in Exod 3 and 14 with rank > 750, with counts. (b) Distinct verb forms in Exod 3 and 14 not in the M6 top 300.
- **M11.** For each candidate passage (Jonah chapters, Ruth 1–4, Gen 1:1–2:3, 12:1–9, 22:1–19, 37, Exod 1–2): tokens, coverage at ranks 330, 400, 480, 570, 660, 750, and count of off-list lemmas. Also the 20 narrative chapters with highest coverage at rank 400.
- **M12.** From Lane's own logs after 30 days: seconds per review by item type, reviews per day per new item, minutes per session, sessions per week.
- **M13.** Tokens where OSHB and BHSA parses disagree (after aligning the two texts); count and list.
- **M14.** Whether the source text encodes the short-o qamats distinctly; if not, the list of forms where the transliterator needs an exception.

## Appendix B. Data sources

| Source | Use | Licence as found |
|---|---|---|
| Open Scriptures Hebrew Bible (WLC + lemma + morphology) | All text, lemmas, parses | Text public domain; lemma and morphology CC BY 4.0 |
| ETCBC BHSA | Independent parse cross-check | CC BY-NC 4.0 |
| MACULA Hebrew (Clear Bible) | Token-level English glosses, syntax | CC BY 4.0 (its morphology comes from OSHB) |
| STEPBible data (TBESH lexicon, TAHOT tagged text, BDB formatted) | Gloss seeding, BDB lookup | Repository states CC BY 4.0; confirm |

## Appendix C. Sources

Reading and learning research
- Schmitt, Jiang & Grabe (2011), The percentage of words known in a text and reading comprehension. https://www.lextutor.ca/cover/papers/schmitt_etal_2011.pdf
- Hu & Nation (2000), Unknown vocabulary density and reading comprehension (thesis record). https://ir.wgtn.ac.nz/handle/123456789/24797
- Yanagisawa, Webb & Uchihara (2020), glossing meta-regression. https://www.cambridge.org/core/product/CC53738607B8DCE3404593043CAEF540
- L1 versus L2 glosses meta-analysis (summary). https://www.todoele.net/bibliografia/relative-effects-l1-and-l2-glosses-l2-learning-meta-analysis
- Webb, Uchihara & Yanagisawa (2023), incidental vocabulary learning meta-analysis (summary). https://todoele.net/node/429491
- Nakanishi (2015), meta-analysis of extensive reading. https://scholarshare.temple.edu/entities/publication/6a42a9ee-8c17-408d-b27f-aaa73550db1c
- Hamada (2020), bias-adjusted extensive reading effects. https://pmc.ncbi.nlm.nih.gov/articles/PMC7188915
- Dunlosky et al. (2013), effective learning techniques (APS summary). https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html
- Reading-while-listening overview (Tragant & Vallbona 2018). https://link.springer.com/10.1007/s11145-018-9886-x

Hebrew curricula and readers
- Pratico & Van Pelt chapter sequence (video lecture listing). https://www.biblicaltraining.org/books/basics-of-biblical-hebrew-video-lectures-a-complete-course-for-the-beginner
- Pratico & Van Pelt review, diagnostic approach (JHS). https://jhsonline.org/index.php/jhs/article/download/11556/8874
- Futato, introduction. https://www.eisenbrauns.org/sample_chapter/Futato_introduction.pdf ; course plan https://ecampus.abs.edu/course/info.php?id=972
- Ross review (JHS). https://jhsonline.org/index.php/jhs/article/download/5937/4990
- Kelley description. https://www.slugbooks.com/9780802805980-biblical-hebrew-an-introductory.html
- Fuller & Choi review (JETS). https://www.galaxie.com/article/jets51-1-10
- Garrett & DeRouchie: publisher contents https://bhacademic.bhpublishinggroup.com/product/a-modern-grammar-for-biblical-hebrew-2/ ; Dallaire review https://denverjournal.denverseminary.edu/the-denver-journal-article/a-modern-grammar-for-biblical-hebrew/ ; reader review https://spoiledmilks.com/2017/05/08/review-modern-grammar-biblical-hebrew-garrett-derouchie/
- Cook & Holmstedt, authors' description. https://www.booksataglance.com/blog/beginning-biblical-hebrew-by-john-a-cook-and-robert-d-holmstedt/
- Kittel, Hoffer & Wright. https://three-things.ca/inductive-grammars/
- Buth / Biblical Language Center. https://thepatrologist.com/interviews-with-communicative-greek-teachers-8-randall-buth/ ; https://logosonlineschool.com/products/copy-of-biblical-hebrew
- A Reader's Hebrew Bible review. https://www.thegospelcoalition.org/themelios/review/a-readers-hebrew-bible/ ; editor interview https://sharperiron.org/node/10745
- BHS Reader's Edition review. https://www.galaxie.com/article/bbr25-3-06

Data
- OSHB. https://github.com/openscriptures/morphhb
- BHSA licence. https://github.com/ETCBC/bhsa
- MACULA Hebrew. https://github.com/Clear-Bible/macula-hebrew ; provenance of its morphology https://www.balisage.net/Proceedings/vol27/html/Robie01/BalisageVol27-Robie01.html
- STEPBible data. https://github.com/STEPBible/STEPBible-Data
- OSHB/BHSA morphology comparison (Text-Fabric paper). https://tidsskrift.dk/hiphilnovum/article/view/142740
