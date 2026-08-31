"""
Real Bible usage examples for the ordinary (non-function-word) vocab deck ->
data/vocab_examples.json. Sibling to build_function_word_examples.py, whose
tiered/rotation machinery is for the 44 function words specifically (see
that file's docstring) and stays there unchanged; this file exists because
Lane also wants at least one real example on every other card (2026-08-29).

Why a separate file rather than folding into function_word_examples.json:
that file's TIER_TARGET (3/5/10 examples, sense-count scaling) exists
because function words are ambiguous -- a bare gloss like "in, on, with"
needs several occurrences to actually disambiguate. An ordinary noun or verb
isn't ambiguous the same way; the point of an example here is reading
fluency and pattern recognition, not sense disambiguation, so one good,
verified occurrence is the target, not a tiered minimum. Sharing the same
per-entry schema (lemma_id/citation_form/transliteration/full_gloss/
sense_count/examples[]) means app/main.js just merges this file's byLemma
map with function_word_examples.json's before handing both to vocab.js --
cardEl/cardBackEl don't know or care which file an example came from.

Scope and priority, per Lane: every drillable vocab_deck_600.json entry NOT
already covered by function_word_examples.json (544 lemmas as of this
writing). Verbs first, then adjectives, then everything else (nouns,
pronouns, adverbs) -- POS_PRIORITY below, not alphabetical or by lemma_id.
Done in batches, not one giant sweep: CURATED holds lemmas with a finished,
verified example; SKIPPED holds lemmas Lane said to file away rather than
force ("unclear examples with broad usage or no clear translation")
alongside why; anything in the target set that's in neither is silently
still PENDING for a future batch -- tracked in metadata.pending_count so
progress is visible, but never a build failure the way an *unexplained*
gap in the function-word set is. A lemma in both CURATED and SKIPPED, or in
SKIPPED, without a reason is still a hard error -- ambiguity about a
lemma's own status is a bug, absence from both is just unfinished work.

Same non-hand-typed-Hebrew discipline as build_function_word_examples.py:
CURATED only records (book_code, target word id, phrase start/end word id,
gloss, gloss_highlight, gloss_note) tuples; the actual Hebrew, its
transliteration, and target_index are all pulled from the corpus and
verified against the claimed lemma at build time, identically to that
file (see its docstring for the full rationale). pipeline/
find_lemma_occurrences.py is a throwaway lookup tool (not part of the
pipeline itself) used to find real word ids worth picking from, rather
than guessing them.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hebrew_corpus import OSIS_NS, WLC_DIR  # noqa: E402
from transliterate import transliterate  # noqa: E402
from build_function_word_examples import (  # noqa: E402
    strip_cantillation, load_book, matches_lemma, extract_phrase,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DECK_PATH = os.path.join(HERE, "..", "data", "vocab_deck_600.json")
FWEX_PATH = os.path.join(HERE, "..", "data", "function_word_examples.json")
OUT_PATH = os.path.join(HERE, "..", "data", "vocab_examples.json")

# Batch 1 (2026-08-29): first 20 highest-frequency verbs. Sourced from
# Genesis 1-8 (creation/flood narrative, not yet a reader chapter but the
# plainest possible Hebrew) and Jonah/Ruth (both already-read reader
# chapters) for variety -- deliberately not all Genesis, per the same
# "too repetitive and Genesis-heavy" note that shaped the function-word
# batches.
CURATED = {
    "H559": [("Gen", "01thY", "01thY", "01JM7", "God said", "said", None)],
    "H1961": [("Gen", "01yw4", "01yw4", "01jbg", "there was light", "was", None)],
    "H6213": [("Gen", "01bmv", "01bmv", "01FV9", "God made", "made", None)],
    "H935": [("Jonah", "32gBW", "32gBW", "32eLD", "to enter the city", "enter", None)],
    "H5414": [("Gen", "012gM", "012gM", "01pAw", "I have given [it] to you", "given", None)],
    "H7200": [("Gen", "01USR", "01USR", "01v6U", "God saw", "saw", None)],
    "H8085": [("Gen", "01S67", "01S67", "014Yz", "you listened to your wife", "listened", "lit. \"to the voice of\" -- shama` + le- idiomatically means listen to/obey, not just hear")],
    "H1696": [("Gen", "01ZXK", "01ZXK", "01frz", "God spoke", "spoke", None)],
    "H3427": [("Ruth", "08wM5", "08wM5", "08qty", "they lived there", "lived", None)],
    "H3318": [("Jonah", "32LsC", "32LsC", "32LzS", "Jonah went out of the city", "went out", None)],
    "H7725": [("Ruth", "08tKT", "08tKT", "08sRU", "she returned from the fields of Moab", "returned", None)],
    "H3212": [("Ruth", "08LN3", "08LN3", "08Qzf", "a man went", "went", None)],
    "H3947": [("Ruth", "08E57", "08E57", "08vtM", "Boaz took Ruth", "took", None)],
    "H3045": [("Jonah", "32AxB", "32oAj", "32Ap3", "for the men knew", "knew", None)],
    "H5927": [("Ruth", "08rzR", "08KTp", "08bh3", "Boaz went up to the gate", "went up", None)],
    "H7971": [("Gen", "01kTA", "01kTA", "01rRy", "he sent out the dove", "sent out", None)],
    "H4191": [("Ruth", "08nAB", "08nAB", "08kfX", "Elimelech died", "died", None)],
    "H398": [("Ruth", "08nzj", "08nzj", "083Sx", "eat some of the bread", "eat", None)],
    "H7121": [("Jonah", "32PB6", "32PB6", "3237c", "and call out against it", "call out", None)],
    "H5375": [("Jonah", "32ecS", "32ecS", "32Xzm", "they lifted up Jonah", "lifted up", None)],

    # Batch 2 (2026-08-29): next 20 verbs by frequency, same Genesis 1-8 /
    # Jonah / Ruth sourcing for variety.
    "H6965": [("Jonah", "32TZE", "32TZE", "32thY", "Jonah got up", "got up", None)],
    "H7760": [("Gen", "01irW", "01irW", "01x72", "he placed [the man] there", "placed", None)],
    "H5674": [("Ruth", "08eHZ", "08A76", "08eHZ", "the redeemer was passing by", "passing by", None)],
    "H5975": [("Jonah", "32uXX", "32uXX", "32xCL", "the sea stood [still]", "stood", None)],
    "H1980": [("Ruth", "08jP7", "08jP7", "08jv3", "go to the vessels", "go", None)],
    "H5221": [("Jonah", "32ht4", "32ht4", "32pYb", "it struck the plant", "struck", None)],
    "H3205": [("Ruth", "08h1i", "08h1i", "08c5a", "she bore a son", "bore", None)],
    "H6680": [("Gen", "01RFe", "01RFe", "01AwN", "the LORD God commanded", "commanded", None)],
    "H8104": [("Gen", "01S3d", "01sCi", "01S3d", "to work it and keep it", "keep", None)],
    "H4672": [("Jonah", "32v6U", "32v6U", "325SS", "he found a ship", "found", None)],
    "H5307": [("Ruth", "083t6", "083t6", "08LDn", "she fell on her face", "fell", None)],
    "H3381": [("Jonah", "32jbg", "32jbg", "32USR", "he went down to Joppa", "went down", None)],
    "H1129": [("Gen", "012oH", "012oH", "01wQL", "the LORD God built [it]", "built", "of God fashioning the rib into a woman, not literal construction")],
    "H5046": [("Jonah", "32LFW", "32j63", "32FbT", "for he had told them", "told", None)],
    "H4427": [("Gen", "01xVz", "01xVz", "01eRE", "Bela became king in Edom", "became king", None)],
    "H1288": [("Gen", "01kDf", "01kDf", "01WPn", "God blessed them", "blessed", None)],
    "H3372": [("Gen", "01m49", "013dA", "01HAZ", "do not fear, Abram", "fear", None)],
    "H6030": [("Ruth", "08p7s", "08p7s", "08ZBR", "Boaz answered", "answered", None)],
    "H6485": [("Ruth", "08L7t", "08L7t", "08xdF", "the LORD had visited his people", "visited", None)],
    "H5493": [("Ruth", "08rKT", "08rKT", "08rHh", "turn aside, sit here", "turn aside", None)],

    # Batch 3 (2026-08-30): next 20 verbs by frequency. katav has no
    # Genesis/Jonah/Ruth occurrence, so sourced from Exodus instead.
    "H2388": [("Gen", "01hfu", "01hfu", "01Luf", "the men seized his hand", "seized", None)],
    "H3772": [("Gen", "01yTL", "01yTL", "01cZp", "the LORD made a covenant with Abram", "made a covenant", "lit. \"cut\" a covenant -- karat's core sense is to cut/sever")],
    "H5647": [("Gen", "01sCi", "01sCi", "01S3d", "to work it and keep it", "work", None)],
    "H341": [("Gen", "01J3C", "01Qi4", "01J3C", "the gate of his enemies", "enemies", "a Qal participle (\"those who are hostile\") used as a noun, not a finite verb form")],
    "H7126": [("Jonah", "32sRU", "32sRU", "32Wxq", "he approached him", "approached", None)],
    "H2421": [("Gen", "01Anx", "01Anx", "01kWB", "Adam lived", "lived", None)],
    "H4390": [("Gen", "01RCg", "01RCg", "01qVd", "fill the waters", "fill", None)],
    "H2398": [("Gen", "012ps", "01UR1", "01DM4", "how have I sinned against you", "sinned", None)],
    "H2142": [("Jonah", "32jjy", "326JA", "32jjy", "I remembered the LORD", "remembered", None)],
    "H7235": [("Gen", "01DDb", "01cK8", "01DDb", "be fruitful and multiply", "multiply", None)],
    "H3423": [("Gen", "01iih", "01iih", "01vUK", "he is my heir", "heir", "lit. \"inherits/possesses me\" -- yarash's core sense is to take possession")],
    "H3789": [("Exod", "02XSs", "02XSs", "02gF9", "Moses wrote", "wrote", None)],
    "H1245": [("Ruth", "0831Z", "0831Z", "08qjY", "shall I seek rest for you", "seek", None)],
    "H3559": [("Gen", "01KDA", "01KDA", "01RvZ", "the matter is certain", "certain", "kun's core sense is to be firm/established -- here of a decision being fixed, not physically built")],
    "H8354": [("Gen", "015dP", "015dP", "01Wke", "he drank from the wine", "drank", None)],
    "H5186": [("Gen", "018NY", "018NY", "01BdS", "he pitched his tent", "pitched", "lit. \"stretched out/extended\" -- natah's core sense, here idiomatically \"pitch a tent\"")],
    "H5800": [("Gen", "01Gpp", "01Gpp", "01T85", "a man shall leave [his father]", "leave", None)],
    "H5337": [("Gen", "01bNf", "01bNf", "01gYW", "God delivered [it]", "delivered", "here of God transferring Laban's flocks to Jacob, not a rescue from danger")],
    "H7901": [("Jonah", "32tKT", "32tKT", "32NRT", "he lay down and fell asleep", "lay down", None)],
    "H157": [("Gen", "018Fj", "01ESV", "018Fj", "whom you love", "love", None)],

    # Batch 4 (2026-08-30): next 20 verbs. yasha` and lakham have no
    # Genesis/Jonah/Ruth occurrence -- both sourced from Exodus 14, one of
    # CLAUDE.md's target reading chapters, which is a bonus fit.
    "H3254": [("Gen", "01Hod", "01Hod", "01LbG", "she bore [him] again", "again", None)],
    "H3467": [("Exod", "026Da", "026Da", "02C4U", "the LORD saved [Israel]", "saved", None)],
    "H3615": [("Gen", "01Hnw", "01Hnw", "01pXi", "God finished", "finished", None)],
    "H8199": [("Gen", "01ujg", "01ujg", "01n8U", "may the LORD judge", "judge", None)],
    "H622": [("Gen", "01g5k", "01g5k", "01wJN", "gather [food] to yourself", "gather", None)],
    "H3201": [("Jonah", "327mS", "32cn3", "327mS", "but they were not able", "able", None)],
    "H7311": [("Gen", "015TM", "015TM", "01ygk", "it rose above the earth", "rose", None)],
    "H1540": [("Gen", "01CFi", "01CFi", "01Ksw", "God had revealed himself to him", "revealed", "a Niphal (reflexive) form -- galah's core sense is to uncover/reveal")],
    "H7650": [("Gen", "01qYw", "01qYw", "01gBf", "swear to me", "swear", None)],
    "H6": [("Jonah", "326qf", "32CZB", "326qf", "let us not perish", "perish", None)],
    "H3898": [("Exod", "02nt7", "02VX2", "02Pk3", "the LORD will fight for you", "fight", None)],
    "H7592": [("Gen", "01xy2", "01xy2", "01Tpm", "I asked her", "asked", None)],
    "H7812": [("Gen", "01bdm", "01bdm", "01qiM", "he bowed down to the ground", "bowed down", None)],
    "H6942": [("Gen", "01jv3", "01jv3", "01ggL", "he sanctified it", "sanctified", None)],
    "H995": [("Gen", "01PSv", "01zs3", "01PSv", "a discerning man", "discerning", None)],
    "H977": [("Gen", "01ino", "01ino", "01ZsF", "Lot chose for himself", "chose", None)],
    "H2026": [("Gen", "01c5a", "01c5a", "01c5a", "he killed him", "killed", None)],
    "H1875": [("Gen", "01pvb", "01Ygk", "01pvb", "she went to inquire [of the LORD]", "inquire", None)],
    "H1984": [("Gen", "01RiY", "01RiY", "01ZhF", "they praised her", "praised", None)],
    "H7462": [("Gen", "015oN", "01mQU", "01HQC", "Abel was a shepherd of sheep", "shepherd", None)],

    # Batch 5 (2026-08-30): next 20 verbs.
    "H2930": [("Gen", "011sW", "011sW", "01tto", "he had defiled Dinah", "defiled", None)],
    "H5127": [("Gen", "01Fm5", "01Fm5", "01KQn", "the king of Sodom fled", "fled", None)],
    "H5608": [("Gen", "01pJA", "01pJA", "01T7j", "count the stars", "count", None)],
    "H5437": [("Jonah", "32aSJ", "32aSJ", "32Kz2", "the weeds wrapped around me", "wrapped around", None)],
    "H8055": [("Jonah", "32eWA", "32eWA", "32CqN", "Jonah rejoiced", "rejoiced", None)],
    "H3680": [("Gen", "01f6y", "01f6y", "01etw", "all the mountains were covered", "covered", None)],
    "H5060": [("Gen", "01pvY", "01LG5", "01pvY", "you shall not touch it", "touch", None)],
    "H7665": [("Jonah", "32hh7", "32NFp", "32hh7", "the ship was about to break apart", "break apart", None)],
    "H8130": [("Gen", "01xTu", "01VUz", "01hya", "you have hated me", "hated", None)],
    "H7843": [("Gen", "01XKu", "018w5", "01XKu", "it was corrupt", "corrupt", None)],
    "H5265": [("Gen", "012W4", "012W4", "01Uzr", "Abram set out", "set out", None)],
    "H6605": [("Gen", "01nTK", "01nTK", "01sBD", "Noah opened [the window]", "opened", None)],
    "H7291": [("Gen", "01nXq", "01nXq", "01WDZ", "he pursued as far as Dan", "pursued", None)],
    "H2490": [("Gen", "01ZkJ", "01LaJ", "01rrP", "when man began [to multiply]", "began", "khalal's \"begin\" sense (Hiphil) -- distinct from its unrelated \"profane/defile\" sense")],
    "H2583": [("Gen", "01SPW", "01SPW", "01T6R", "he camped in the valley of Gerar", "camped", None)],
    "H6437": [("Gen", "01evQ", "01evQ", "01NA8", "the men turned away from there", "turned", None)],
    "H2076": [("Jonah", "32xAF", "32xAF", "326w9", "they offered a sacrifice to the LORD", "offered a sacrifice", None)],
    "H6912": [("Ruth", "08Qnr", "08xCL", "08Qnr", "there I will be buried", "buried", None)],
    "H7604": [("Ruth", "083TL", "083TL", "08LeN", "she was left [with her two sons]", "was left", None)],
    "H7931": [("Gen", "01Xv2", "01Xv2", "01qDj", "let him dwell in the tents of Shem", "dwell", None)],

    # Batch 6 (2026-08-30): next 20 verbs. lakhad/batakh/qatar/nava' have no
    # Genesis/Jonah/Ruth occurrence, sourced from Joshua/Psalms/Leviticus/
    # Jeremiah instead.
    "H6908": [("Gen", "01Kg2", "01Kg2", "01Kg2", "he gathered", "gathered", None)],
    "H5066": [("Ruth", "08BFZ", "08BFZ", "08shy", "come here", "come", "lit. \"approach/draw near\" -- nagash's core sense; \"goshi halom\" is an idiom, \"draw near here\"")],
    "H7993": [("Gen", "01meh", "01meh", "01jYS", "she put the child [under a bush]", "put", "lit. \"threw/cast\" -- shalakh's core sense; here of Hagar setting Ishmael down, not violent throwing (distinct root from H7971 \"send\")")],
    "H2803": [("Gen", "01awo", "01awo", "01FpW", "he credited it to him", "credited", "of Abram's faith counted as righteousness (Gen 15:6)")],
    "H3920": [("Josh", "06CXn", "06CXn", "06z2s", "they captured the city", "captured", None)],
    "H982": [("Ps", "19KGj", "19KGj", "198xz", "let them trust in you", "trust", None)],
    "H6999": [("Lev", "03Qsh", "03Qsh", "03zTj", "the priest burned it [on the altar]", "burned", "Hiphil of qatar -- to turn into smoke/burn as an offering, not ordinary burning")],
    "H8210": [("Gen", "01cw6", "01BDF", "01cw6", "his blood shall be shed", "shed", None)],
    "H8313": [("Gen", "01D4i", "01D4i", "01qRk", "let us burn [them] thoroughly", "burn", "of firing bricks (Tower of Babel), not a punishment")],
    "H1058": [("Ruth", "08TXw", "08TXw", "08TXw", "they wept", "wept", None)],
    "H1431": [("Gen", "0156w", "0156w", "01h2d", "I will make your name great", "great", None)],
    "H3513": [("Gen", "01Pf6", "01Zh8", "01Pf6", "Abram was very wealthy", "wealthy", "lit. \"heavy\" -- kavad's core sense; here idiomatically of great material wealth")],
    "H7999": [("Ruth", "08FyK", "08FyK", "08jaD", "may the LORD repay your deeds", "repay", None)],
    "H5012": [("Jer", "24prm", "24oG9", "24prm", "the prophets prophesied", "prophesied", None)],
    "H3034": [("Gen", "01hti", "01nGF", "01KTs", "this time I will praise the LORD", "praise", None)],
    "H954": [("Gen", "01rio", "01fE2", "01rio", "they were not ashamed", "ashamed", None)],
    "H3190": [("Jonah", "32AF1", "32AF1", "32zCS", "is it right for you to be angry", "right", "lit. \"is it good\" -- yatav's core sense; the LORD questioning Jonah's anger")],
    "H3847": [("Jonah", "32e3z", "32e3z", "322c6", "they put on sackcloth", "put on", None)],
    "H5162": [("Gen", "01jsC", "01jsC", "01VLV", "the LORD regretted [making humanity]", "regretted", None)],
    "H539": [("Jonah", "32eN1", "32eN1", "325QX", "the people of Nineveh believed God", "believed", None)],

    # Batch 7 (2026-08-30): next 20 verbs. ba`ar's clearest occurrence is
    # the burning bush (Exodus 3, a CLAUDE.md target chapter).
    "H3498": [("Gen", "01tFY", "01tFY", "01Hbx", "Jacob was left alone", "left", None)],
    "H1350": [("Ruth", "08bvs", "08y7z", "08Gxe", "for you are a redeemer", "redeemer", None)],
    "H7323": [("Gen", "01cpk", "01cpk", "01mqu", "Abraham ran", "ran", None)],
    "H3722": [("Gen", "01min", "01min", "01iic", "you shall coat it [with pitch]", "coat", "here of waterproofing the ark; kafar's more common sense in the Torah is \"atone/make atonement\", related to covering")],
    "H7489": [("Jonah", "32FyK", "32FyK", "32XjR", "it displeased Jonah greatly", "displeased", "idiom: ra`a` + 'el = be evil/displeasing to")],
    "H7911": [("Gen", "016ta", "016ta", "016ta", "he forgot him", "forgot", None)],
    "H7125": [("Gen", "01Gbm", "01Gbm", "01Gbm", "to meet him", "meet", None)],
    "H1481": [("Ruth", "08qNN", "08qNN", "08PB6", "to sojourn in the fields of Moab", "sojourn", None)],
    "H8334": [("Gen", "01YgJ", "01YgJ", "01wF3", "he served him", "served", None)],
    "H7646": [("Ruth", "08AF1", "08m55", "08AF1", "she ate and was satisfied", "satisfied", None)],
    "H2891": [("Gen", "01Lmg", "01Lmg", "01Lmg", "purify yourselves", "purify", None)],
    "H4422": [("Gen", "01coZ", "01B9T", "01coZ", "I am not able to escape", "escape", None)],
    "H1197": [("Exod", "02w6U", "02g5u", "02ifL", "the bush was burning with fire", "burning", None)],
    "H2015": [("Jonah", "32S38", "32QvZ", "32S38", "Nineveh shall be overturned", "overturned", None)],
    "H2181": [("Gen", "01nXv", "01jJh", "01nXv", "he thought her a prostitute", "prostitute", "of Tamar disguised, Gen 38")],
    "H5462": [("Gen", "01FXw", "01FXw", "01roj", "the LORD shut him in", "shut", None)],
    "H2734": [("Gen", "01b2J", "015on", "01MnD", "why are you angry", "angry", None)],
    "H8045": [("Gen", "01pUz", "01pUz", "01GbB", "I will be destroyed", "destroyed", None)],
    "H7891": [("Exod", "02gWC", "02LQN", "02c6U", "then Moses sang", "sang", None)],
    "H3885": [("Gen", "01Ue8", "01Ue8", "01Ue8", "and spend the night [here]", "spend the night", None)],

    # Batch 8 (2026-08-30): next 20 verbs. lamad/shamem/`ur/ya`ats/ma'as
    # have no Genesis/Jonah/Ruth occurrence, sourced from Deuteronomy,
    # Leviticus, Judges, 2 Samuel, and 1 Samuel instead.
    "H3925": [("Deut", "05eof", "05eof", "05x6W", "I have taught you statutes", "taught", None)],
    "H3384": [("Gen", "01Ykc", "01Ykc", "01V5w", "to show the way ahead of him", "show", "Hiphil of yarah (\"teach/direct\"), lit. \"to point out/instruct\"")],
    "H7069": [("Gen", "01jGt", "01jGt", "01tyS", "I have acquired a man", "acquired", "Eve naming Cain (qayin), a wordplay on qanah")],
    "H7896": [("Gen", "01EyU", "01Xh3", "01EyU", "I will put enmity [between you]", "put", None)],
    "H8074": [("Lev", "03Awo", "03Awo", "03yn6", "I will make your sanctuaries desolate", "desolate", None)],
    "H6419": [("Jonah", "321jv", "321jv", "32RCg", "Jonah prayed to the LORD", "prayed", None)],
    "H6031": [("Gen", "016Yk", "016Yk", "01yaX", "Sarai afflicted her", "afflicted", None)],
    "H4910": [("Gen", "01n9v", "01n9v", "01gYe", "to rule the day", "rule", None)],
    "H5641": [("Gen", "017Xe", "01nM3", "017Xe", "from your face I will be hidden", "hidden", None)],
    "H5826": [("Gen", "01dgN", "01dgN", "01dgN", "may he help you", "help", None)],
    "H7043": [("Gen", "01CUd", "01W19", "01dBb", "the waters had subsided", "subsided", "lit. \"were light/diminished\" -- qalal's core sense; here of floodwaters receding, distinct from its more common \"curse\" sense")],
    "H7819": [("Gen", "01rb5", "01rb5", "01URH", "to slaughter his son", "slaughter", None)],
    "H4376": [("Gen", "01ZMA", "01ZMA", "01rm7", "he sold his birthright", "sold", None)],
    "H5782": [("Judg", "07CVL", "07CVL", "079vz", "awake, awake", "awake", None)],
    "H2603": [("Gen", "01ASY", "01hWa", "01HYe", "whom God has graciously given [your servant]", "graciously given", None)],
    "H3289": [("2Sam", "10N8y", "10rif", "10N8y", "which he advised", "advised", None)],
    "H7392": [("Gen", "01AfW", "01AfW", "01qni", "they rode on the camels", "rode", None)],
    "H3988": [("1Sam", "09fVR", "09ZoM", "09fVR", "they have not rejected you", "rejected", None)],
    "H6186": [("Gen", "012HK", "012HK", "01PUW", "he arranged the wood", "arranged", None)],
    "H2470": [("Gen", "01PJe", "01J66", "01PJe", "your father is sick", "sick", None)],

    # Batch 9 (2026-08-30): final 19 verbs -- completes all 179.
    "H2654": [("Jonah", "32Ddq", "32chR", "32Ddq", "as you have desired", "desired", None)],
    "H3240": [("Gen", "01vdQ", "01vdQ", "01HK3", "he placed him in the garden of Eden", "placed", None)],
    "H5324": [("Gen", "01nre", "01fnW", "01nre", "men were standing [before him]", "standing", None)],
    "H2199": [("Jonah", "328M6", "328M6", "325gQ", "they cried out, each to his god", "cried out", None)],
    "H3001": [("Jonah", "32g5u", "32g5u", "32g5u", "it withered", "withered", None)],
    "H631": [("Gen", "012iV", "01cVC", "012iV", "Joseph was imprisoned there", "imprisoned", None)],
    "H2790": [("Gen", "01kBL", "01kBL", "01ae2", "Jacob remained silent", "remained silent", "Hiphil of kharash -- \"be silent\" sense; the root's other core senses are \"engrave/plow\"")],
    "H7364": [("Gen", "01CQM", "01CQM", "01MHE", "wash your feet", "wash", None)],
    "H6381": [("Gen", "01Kzw", "01Kzw", "01t9h", "is anything too wonderful for the LORD", "wonderful", None)],
    "H7673": [("Gen", "01CMD", "01CMD", "01Cj2", "he rested on the seventh day", "rested", None)],
    "H5027": [("Gen", "01bD6", "01bD6", "01S4Y", "look now toward the heavens", "look", None)],
    "H7378": [("Gen", "012Yq", "012Yq", "01v8s", "the herdsmen of Gerar quarreled", "quarreled", None)],
    "H8628": [("Gen", "01fr8", "01iBK", "01fr8", "Jacob pitched his tent", "pitched", "lit. \"thrust/drove in\" (tent pegs) -- taqa`'s core sense; also used for blowing a trumpet")],
    "H4886": [("Gen", "01jH9", "01f4t", "01jH9", "where you anointed [a pillar]", "anointed", None)],
    "H7495": [("Gen", "019iL", "019iL", "01N3B", "God healed Abimelech", "healed", None)],
    "H270": [("Gen", "019SJ", "01rFn", "019SJ", "a ram was caught [in the thicket]", "caught", None)],
    "H6327": [("Gen", "01FD2", "01wVX", "01FD2", "lest we be scattered [over all the earth]", "scattered", None)],
    "H5117": [("Gen", "01QL7", "01QL7", "01cRW", "the ark came to rest", "rest", None)],
    "H6566": [("Ruth", "08XwG", "08XwG", "08iPC", "spread your wing over [your servant]", "spread", None)],

    # Batch 10 (2026-08-30): all 44 adjectives. yashar/qadosh/tame'/`ani/
    # zur/kesil have no Genesis/Jonah/Ruth occurrence, sourced from
    # Deuteronomy, Exodus, Leviticus, and Proverbs instead.
    "H259": [("Gen", "01NFp", "013TS", "01NFp", "one day", "one", None)],
    "H8147": [("Gen", "01YHH", "01YHH", "01sHf", "the two great lights", "two", None)],
    "H7451": [("Gen", "015ED", "01AF1", "015ED", "good and evil", "evil", None)],
    "H3967": [("Gen", "01nfi", "01bu5", "01nfi", "eight hundred years", "hundred", None)],
    "H2896": [("Gen", "01g2y", "01qCU", "01g2y", "that it was good", "good", None)],
    "H1419": [("Gen", "01iee", "01sHf", "01iee", "the great lights", "great", None)],
    "H505": [("Gen", "01PdT", "01xhg", "01VCX", "I have given a thousand [pieces] of silver", "thousand", None)],
    "H7227": [("Gen", "01mM8", "01zBj", "01mM8", "that [man's wickedness] was great", "great", None)],
    "H7969": [("Gen", "01Lrp", "01Lrp", "01c4q", "three hundred years", "three", None)],
    "H7651": [("Gen", "015VT", "015VT", "018JC", "seven years", "seven", None)],
    "H2568": [("Gen", "01nnJ", "01nnJ", "01b2r", "five years", "five", None)],
    "H6240": [("Gen", "01jDT", "01RZe", "01jDT", "twelve years", "twelve", "`asar/`esreh is the \"-teen\" suffix combined with a ones digit (here sheteym `esreh = twelve), not a standalone word for \"ten\" (that's `eser, a separate lemma)")],
    "H702": [("Gen", "01Ekx", "016bH", "01Ekx", "it became four [heads]", "four", None)],
    "H6242": [("Gen", "01peT", "01T55", "01peT", "a hundred and twenty years", "twenty", None)],
    "H7563": [("Gen", "01iLp", "01WEE", "01iLp", "righteous with the wicked", "wicked", None)],
    "H8337": [("Gen", "01UWF", "01UWF", "012Ha", "six hundred years", "six", None)],
    "H6662": [("Gen", "01QzN", "01rsj", "01zQg", "a righteous, blameless man", "righteous", None)],
    "H7223": [("Gen", "015tL", "015tL", "01Pj9", "in the first [month]", "first", None)],
    "H2205": [("Gen", "01zTW", "01jqR", "01zTW", "Abraham and Sarah were old", "old", None)],
    "H6235": [("Gen", "01YsH", "01JVU", "01YsH", "at the end of ten years", "ten", None)],
    "H7970": [("Gen", "0126j", "0126j", "01ZiN", "thirty and a hundred years", "thirty", None)],
    "H312": [("Gen", "01MWU", "01Hwq", "01MWU", "another offspring", "another", None)],
    "H2572": [("Gen", "01kST", "01kST", "01G8f", "fifty cubits its width", "fifty", None)],
    "H1368": [("Gen", "0162h", "019F4", "0162h", "he began to be a mighty man", "mighty", "of Nimrod, Gen 10:8")],
    "H8145": [("Gen", "0187B", "01Snp", "0187B", "a second day", "second", None)],
    "H2450": [("Gen", "01kMw", "01zs3", "01kMw", "a discerning and wise man", "wise", None)],
    "H705": [("Gen", "01ngx", "01ngx", "019eB", "forty days", "forty", None)],
    "H3477": [("Deut", "05HnC", "05WDj", "05HnC", "you shall do what is right", "right", None)],
    "H6918": [("Exod", "026DP", "02pQs", "026DP", "and a holy nation", "holy", None)],
    "H8083": [("Gen", "01bu5", "01bu5", "01nfi", "eight hundred years", "eight", None)],
    "H7992": [("Gen", "01oAj", "01sKn", "01oAj", "a third day", "third", None)],
    "H6996": [("Gen", "01dSQ", "01U4a", "01dSQ", "the lesser light", "lesser", None)],
    "H7637": [("Gen", "01rZH", "01Nq4", "01rZH", "on the seventh day", "seventh", None)],
    "H2491": [("Gen", "016Ep", "016GM", "016Ep", "[they] came upon the slain", "slain", "of Shechem, Gen 34:27")],
    "H2889": [("Lev", "03kav", "032iX", "03enN", "every clean [animal] may be eaten", "clean", None)],
    "H7657": [("Gen", "01BKq", "01BKq", "01zK3", "seventy years", "seventy", None)],
    "H8549": [("Gen", "01SxU", "01S4D", "01SxU", "be blameless", "blameless", None)],
    "H2931": [("Lev", "03KGK", "03Lz7", "03KGK", "any unclean thing", "unclean", None)],
    "H7350": [("Gen", "01oMA", "01Df6", "01oMA", "he saw the place from afar", "from afar", None)],
    "H2145": [("Gen", "01gc8", "01pUN", "01Lsp", "male and female he created them", "male", None)],
    "H6041": [("Exod", "02vyC", "02cYr", "02vyC", "the poor [among you]", "poor", None)],
    "H7138": [("Gen", "01WqV", "01H37", "01YgK", "you shall be near me", "near", None)],
    "H2114": [("Exod", "02qBE", "02qBE", "02LSn", "an outsider shall not eat [it]", "outsider", "zur's participle used substantively (\"one who is estranged/a stranger\"), not describing the verb's action directly")],
    "H3684": [("Prov", "20dAC", "20GvF", "20dAC", "the complacency of fools", "fools", None)],

    # Batch 11 (2026-08-30): first 20 nouns/pronouns by frequency.
    "H3068": [("Gen", "01gcK", "01M7H", "01p7s", "when the LORD God made", "LORD", None)],
    "H3605": [("Gen", "01xAF", "01xAF", "016w9", "every living creature", "every", None)],
    "H1121": [("Gen", "01UeD", "01Mef", "01UeD", "after the name of his son", "son", None)],
    "H430": [("Gen", "01TyA", "01Nvk", "01TyA", "God created", "God", None)],
    "H4428": [("Gen", "01BFg", "01Tdr", "01T8E", "Amraphel king of Shinar", "king", None)],
    "H3478": [("Gen", "01Q1E", "01Q1E", "01Q1E", "Israel", "Israel", None)],
    "H776": [("Gen", "01nPh", "01nPh", "01nPh", "the earth", "earth", None)],
    "H3117": [("Gen", "013TS", "013TS", "01NFp", "one day", "day", None)],
    "H376": [("Gen", "01T85", "01Gpp", "01T85", "a man shall leave [his father]", "man", None)],
    "H6440": [("Gen", "01EVS", "01qNN", "01PB6", "upon the face of the deep", "face", None)],
    "H1004": [("Gen", "01LrK", "01pSV", "01LrK", "and all your household", "household", None)],
    "H1931": [("Gen", "01ELV", "01XSi", "01ELV", "Pishon -- it is the one that flows around", "it", None)],
    "H5971": [("Gen", "01WQT", "01LrY", "01m63", "behold, one people", "people", None)],
    "H3027": [("Gen", "01Wgd", "01Wgd", "01Wgd", "from your hand", "hand", None)],
    "H1697": [("Gen", "0142S", "0142S", "01rNq", "and the same words", "words", None)],
    "H1": [("Gen", "01XZe", "01Jrt", "01XZe", "he was the father [of tent-dwellers]", "father", None)],
    "H2088": [("Gen", "015Xt", "015Xt", "018jj", "this is the book", "this", None)],
    "H859": [("Gen", "01ZgJ", "01WMb", "01ZgJ", "cursed are you", "you", None)],
    "H5892": [("Gen", "01D9B", "01QR7", "01D9B", "he was building a city", "city", None)],
    "H1732": [("Ruth", "08AuA", "08DR2", "08AuA", "and Jesse fathered David", "David", None)],

    # Batch 12 (2026-08-30): next 20 nouns/pronouns/adverbs. mosheh and
    # yerushalam have no Genesis occurrence, sourced from Exodus/Joshua.
    "H5869": [("Gen", "01P1s", "01YfW", "01P1s", "your eyes will be opened", "eyes", None)],
    "H8141": [("Gen", "01Axb", "01Axb", "01Axb", "and years", "years", None)],
    "H589": [("Gen", "01T4t", "01T4t", "01CXn", "and as for me, behold", "me", None)],
    "H8034": [("Gen", "01EL8", "01EL8", "01XSi", "the name of the first is Pishon", "name", None)],
    "H8033": [("Gen", "01x72", "01irW", "01x72", "he placed [him] there", "there", None)],
    "H3063": [("Gen", "01uoQ", "01QsQ", "01uoQ", "she called his name Judah", "Judah", None)],
    "H5650": [("Gen", "01N1Q", "01N1Q", "01sKY", "a servant of servants he shall be", "servant", None)],
    "H802": [("Gen", "01ymv", "01ymv", "01ymv", "into a woman", "woman", None)],
    "H4872": [("Exod", "02pAw", "02Ygn", "02pAw", "she called his name Moses", "Moses", None)],
    "H5315": [("Gen", "01dSp", "01dSp", "01ecS", "living creature", "creature", None)],
    "H3548": [("Gen", "014xN", "01cUQ", "014xN", "he was priest [of God Most High]", "priest", None)],
    "H428": [("Gen", "01idA", "01idA", "01Z4D", "these are the generations", "these", None)],
    "H1870": [("Gen", "01fSj", "01UwQ", "01fSj", "to guard the way [to the tree of life]", "way", None)],
    "H3389": [("Josh", "06YgF", "06u5x", "06YgF", "king of Jerusalem", "Jerusalem", None)],
    "H4714": [("Gen", "01GfA", "01GfA", "01GfA", "and Egypt", "Egypt", None)],
    "H251": [("Gen", "01zJw", "01jJf", "01zJw", "his brother", "brother", None)],
    "H2063": [("Gen", "01WMK", "01WMK", "01ctU", "this time/this one", "this", None)],
    "H7218": [("Gen", "01PG7", "01Ekx", "01PG7", "into four heads", "heads", None)],
    "H3820": [("Gen", "01zuP", "01gi1", "01zuP", "the intent of his heart's thoughts", "heart", None)],
    "H1323": [("Gen", "01A4n", "01A4n", "01A4n", "and daughters", "daughters", None)],

    # Batch 13 (2026-08-30): next 20 nouns/adverbs. qodesh's clearest hit
    # is the burning bush -- "it is holy ground" (Exodus 3).
    "H4325": [("Gen", "01TZE", "0129t", "01TZE", "upon the face of the water", "water", None)],
    "H3541": [("Gen", "01WUC", "01WUC", "013VU", "so shall your offspring be", "so", None)],
    "H1471": [("Gen", "01adv", "01b5P", "01adv", "the coastlands of the nations", "nations", None)],
    "H1992": [("Gen", "01pVx", "01HQ9", "01pVx", "that they were naked", "they", None)],
    "H120": [("Gen", "01gPX", "01oiy", "01gPX", "let us make man", "man", None)],
    "H2022": [("Gen", "01etw", "01Gy9", "01GQd", "all the high mountains", "mountains", None)],
    "H6963": [("Gen", "011go", "01PHG", "011go", "they heard the sound [of the LORD]", "sound", None)],
    "H2416": [("Gen", "01ecS", "01dSp", "01ecS", "a living creature", "living", None)],
    "H6310": [("Gen", "01NH6", "01EWV", "01NH6", "has opened its mouth", "mouth", None)],
    "H5750": [("Gen", "0125j", "014VF", "0125j", "Adam knew [his wife] again", "again", None)],
    "H6635": [("Gen", "01EZz", "01taY", "01EZz", "and all their host", "host", None)],
    "H6944": [("Exod", "02njg", "02Wyn", "02L6G", "it is holy ground", "holy", None)],
    "H136": [("Gen", "01w93", "01w93", "01hRC", "O Lord GOD", "Lord", None)],
    "H5769": [("Gen", "01cy3", "01CGY", "01cy3", "and live forever", "forever", None)],
    "H6258": [("Gen", "01tvR", "01tvR", "01tvR", "and now", "now", None)],
    "H4941": [("Gen", "013cG", "01f26", "013cG", "righteousness and justice", "justice", None)],
    "H8064": [("Gen", "01TSc", "01vuQ", "01TSc", "the heavens", "heavens", None)],
    "H8269": [("Gen", "01fBS", "01fBS", "01r2p", "the officials of Pharaoh", "officials", None)],
    "H8432": [("Gen", "018M6", "018M6", "01wM5", "in the midst of the waters", "midst", None)],
    "H2719": [("Gen", "01RZP", "01FUa", "01RZP", "the flame of the sword", "sword", None)],

    # Batch 14 (2026-08-30): next 20 nouns/pronouns. aharon has no
    # Genesis occurrence, sourced from Exodus.
    "H7586": [("Gen", "01pH1", "01KrB", "01pH1", "Saul reigned in his place", "Saul", None)],
    "H3701": [("Gen", "01peM", "01peM", "01dMe", "in silver and gold", "silver", None)],
    "H4196": [("Gen", "01em6", "01LXw", "01em6", "Noah built an altar", "altar", None)],
    "H4725": [("Gen", "01Q7E", "01tRR", "01dv1", "to one place", "place", None)],
    "H3220": [("Gen", "019KV", "01fJN", "019KV", "he called [them] seas", "seas", None)],
    "H2091": [("Gen", "01vwH", "01vwH", "01vwH", "the gold", "gold", None)],
    "H7307": [("Gen", "0137c", "0137c", "01x9c", "and the spirit of God", "spirit", None)],
    "H784": [("Gen", "01hwb", "01icS", "01hwb", "and a flaming torch", "flaming", None)],
    "H5002": [("Gen", "01CmJ", "01CmJ", "01Q6h", "declares the LORD", "declares", None)],
    "H8179": [("Gen", "01kXh", "01SDq", "01URX", "sitting in the gate of Sodom", "gate", None)],
    "H1818": [("Gen", "01jGA", "019Gr", "01Q9B", "the voice of your brother's blood", "blood", None)],
    "H595": [("Gen", "01GFP", "01bcQ", "01GFP", "I was naked", "I", None)],
    "H3290": [("Gen", "01DcB", "01etA", "01DcB", "he called his name Jacob", "Jacob", None)],
    "H168": [("Gen", "01f7v", "01dip", "01f7v", "dwelling in tents", "tents", None)],
    "H175": [("Exod", "02b2J", "025on", "02MnD", "is there not Aaron your brother", "Aaron", None)],
    "H5439": [("Gen", "01av2", "01xBa", "01av2", "all around its border", "around", None)],
    "H7704": [("Gen", "01GmF", "0189r", "01GmF", "the shrub of the field", "field", None)],
    "H6086": [("Gen", "01fV3", "01fV3", "01Sov", "fruit tree", "tree", None)],
    "H113": [("Gen", "01sDg", "01sDg", "01sDg", "my lord", "lord", None)],
    "H3627": [("Gen", "01F4E", "01F4E", "01wMa", "vessels of silver", "vessels", None)],

    # Batch 15 (2026-08-30): next 20 nouns/adverbs. shelomoh and lewiyi
    # have no Genesis occurrence, sourced from 1 Kings and Exodus.
    "H4421": [("Gen", "01Gcz", "015PZ", "01Gcz", "they made war", "war", None)],
    "H5030": [("Gen", "01UMk", "01P7Z", "01yqU", "for he is a prophet", "prophet", None)],
    "H3069": [("Gen", "01hRC", "01w93", "01hRC", "O Lord GOD", "GOD", None)],
    "H4940": [("Gen", "01Lzv", "01Lzv", "01Lzv", "by their families", "families", None)],
    "H3966": [("Gen", "01dPK", "01ce9", "01dPK", "very good", "very", None)],
    "H2403": [("Gen", "01hnA", "01Ggr", "01hnA", "sin is crouching at the door", "sin", None)],
    "H3899": [("Gen", "012Ss", "01c7o", "012Ss", "you shall eat bread", "bread", None)],
    "H6256": [("Gen", "01p6C", "01p6C", "01Dn5", "at the time of evening", "time", None)],
    "H8010": [("1Kgs", "113Lj", "1175P", "113Lj", "the mother of Solomon", "Solomon", None)],
    "H6430": [("Gen", "019Bj", "019Bj", "019Bj", "Philistines", "Philistines", None)],
    "H5930": [("Gen", "01hNg", "01aVY", "01hNg", "he offered burnt offerings", "burnt offerings", None)],
    "H3881": [("Exod", "022B3", "022B3", "022B3", "the Levite", "Levite", None)],
    "H1285": [("Gen", "01yyf", "017nT", "01yyf", "my covenant", "covenant", None)],
    "H2320": [("Gen", "01p5C", "01p5C", "01pLh", "in the second month", "month", None)],
    "H639": [("Gen", "01YQ8", "01YQ8", "01YQ8", "into his nostrils", "nostrils", None)],
    "H6629": [("Gen", "01HQC", "015oN", "01HQC", "a shepherd of sheep", "sheep", None)],
    "H68": [("Gen", "01w7p", "01w7p", "01k7H", "and onyx stone", "stone", None)],
    "H4057": [("Gen", "01XAP", "01Kk2", "01XAP", "by the wilderness", "wilderness", None)],
    "H1320": [("Gen", "01nRw", "0131Z", "01nRw", "he closed up the flesh", "flesh", None)],
    "H6547": [("Gen", "01r2p", "01fBS", "01r2p", "the officials of Pharaoh", "Pharaoh", None)],

    # Batch 16 (2026-08-30): next 20 nouns, all found in Genesis.
    "H894": [("Gen", "01nPn", "01gCC", "01nPn", "the beginning of his kingdom was Babylon", "Babylon", None)],
    "H3824": [("Gen", "01XQZ", "01BMP", "01XQZ", "in the integrity of my heart", "heart", None)],
    "H4294": [("Gen", "01jKF", "01jKF", "01WWp", "and your staff that is in your hand", "staff", None)],
    "H2617": [("Gen", "01M8k", "01W2g", "01M8k", "you have shown great kindness", "kindness", None)],
    "H7272": [("Gen", "019jg", "01SdW", "019jg", "for the sole of her foot", "foot", None)],
    "H520": [("Gen", "015Jx", "01sX9", "015Jx", "three hundred cubits", "cubits", None)],
    "H410": [("Gen", "01rXs", "014xN", "01rXs", "priest of God Most High", "God", None)],
    "H1366": [("Gen", "01tYs", "01sCe", "01SFu", "the territory of the Canaanites was", "territory", None)],
    "H5288": [("Gen", "014we", "01r3M", "014we", "what the young men have eaten", "young men", None)],
    "H7965": [("Gen", "01Hip", "01DAW", "01Hip", "you shall go to your fathers in peace", "peace", None)],
    "H3915": [("Gen", "01sMn", "01LeN", "01sMn", "he called [it] night", "night", None)],
    "H4639": [("Gen", "01zGh", "01zGh", "01zGh", "from our work", "work", None)],
    "H2428": [("Gen", "01qoF", "017JY", "01qoF", "all their wealth", "wealth", None)],
    "H5771": [("Gen", "01Lz7", "01MEe", "01Lz7", "my guilt is greater [than I can bear]", "guilt", None)],
    "H2233": [("Gen", "01VA9", "01Bbz", "01VA9", "yielding seed", "seed", None)],
    "H7130": [("Gen", "01SsZ", "01SsZ", "01SsZ", "within herself", "within", None)],
    "H127": [("Gen", "01zEm", "016zt", "01zEm", "creatures of the ground", "ground", None)],
    "H4150": [("Gen", "01SHw", "01SHw", "01SHw", "and for appointed times", "appointed times", None)],
    "H5159": [("Gen", "01CgJ", "01Q7w", "01CgJ", "portion or inheritance", "inheritance", None)],
    "H8451": [("Gen", "01tND", "01tND", "01tND", "and my instructions", "instructions", None)],

    # Batch 17 (2026-08-30): next 20 nouns. yehoshua` has no Genesis
    # occurrence, sourced from Joshua.
    "H517": [("Gen", "01fiZ", "01E2x", "01fiZ", "and his mother", "mother", None)],
    "H3091": [("Josh", "06aPd", "06Qzf", "06C5U", "the LORD spoke to Joshua son of Nun", "Joshua", None)],
    "H899": [("Gen", "014cr", "014cr", "014cr", "and garments", "garments", None)],
    "H4264": [("Gen", "01ks1", "01ks1", "01HPH", "the camp of God", "camp", None)],
    "H1242": [("Gen", "01kA7", "01uLf", "01kA7", "there was morning", "morning", None)],
    "H3130": [("Gen", "01jSR", "01Pjw", "01jSR", "she called his name Joseph", "Joseph", None)],
    "H4397": [("Gen", "01yqG", "01yqG", "016ev", "the angel of the LORD", "angel", None)],
    "H4503": [("Gen", "0128H", "0128H", "01cog", "an offering to the LORD", "offering", None)],
    "H727": [("Gen", "01dCe", "01xuy", "01dCe", "he was placed in a coffin", "coffin", "of Joseph's coffin in Egypt -- a general word for chest/box, also used for the Ark of the Covenant")],
    "H905": [("Gen", "01vL9", "01vL9", "01vL9", "alone", "alone", None)],
    "H3519": [("Gen", "014m8", "01YZe", "014m8", "all this wealth", "wealth", "kavod's core sense is glory/honor; here idiomatically of Jacob's material prosperity")],
    "H352": [("Gen", "01vxt", "01vxt", "0126U", "and a three-year-old ram", "ram", None)],
    "H3709": [("Gen", "01SdW", "01SdW", "019jg", "for the sole of her foot", "sole", None)],
    "H8081": [("Gen", "01ycr", "01B7Q", "01ycr", "he poured oil", "oil", None)],
    "H2691": [("Gen", "01cGb", "01cGb", "01cGb", "in their settlements", "settlements", None)],
    "H7626": [("Gen", "01ZcT", "01Gzy", "01ZcT", "the scepter shall not depart", "scepter", "shevet's core sense is tribe/rod; here idiomatically \"scepter\", a rod of authority (Jacob's blessing on Judah, Gen 49:10)")],
    "H929": [("Gen", "01ou4", "01xxn", "01ou4", "livestock according to their kinds", "livestock", None)],
    "H7453": [("Gen", "01pyb", "01DaL", "01pyb", "each to his neighbor", "neighbor", None)],
    "H241": [("Gen", "01a92", "01a92", "01a92", "in their ears", "ears", None)],
    "H5612": [("Gen", "018jj", "015Xt", "018jj", "this is the book", "book", None)],

    # Batch 18 (2026-08-30): next 20 nouns. tsiyon/khokhmah have no
    # Genesis occurrence, sourced from Psalms/Proverbs.
    "H4687": [("Gen", "01KPR", "01KPR", "01KPR", "my commandments", "commandments", None)],
    "H1241": [("Gen", "01o5N", "01eLd", "01o5N", "sheep and oxen", "oxen", None)],
    "H3383": [("Gen", "01rN3", "01ti5", "01rN3", "the whole plain of the Jordan", "Jordan", None)],
    "H4124": [("Gen", "01mdG", "014rn", "01mdG", "she called his name Moab", "Moab", None)],
    "H669": [("Gen", "01zCA", "01H1E", "01zCA", "he called [him] Ephraim", "Ephraim", None)],
    "H8193": [("Gen", "01dve", "01dve", "01xj3", "one language", "language", None)],
    "H85": [("Gen", "01TCv", "01Ycg", "01TCv", "your name shall be Abraham", "Abraham", None)],
    "H1755": [("Gen", "01ZxQ", "01ZxQ", "01ZxQ", "in his generations", "generations", None)],
    "H1144": [("Gen", "01bpG", "01Vfn", "01bpG", "he called him Benjamin", "Benjamin", None)],
    "H4399": [("Gen", "01GtT", "01GtT", "01GtT", "his work", "work", None)],
    "H2351": [("Gen", "01fqr", "01uQX", "01fqr", "inside and outside", "outside", None)],
    "H6607": [("Gen", "01Ggr", "01Ggr", "01Ggr", "at the door", "door", None)],
    "H2077": [("Gen", "01TLG", "01wee", "01TLG", "Jacob offered a sacrifice", "sacrifice", None)],
    "H6666": [("Gen", "01Q3M", "01FpW", "01Q3M", "to him as righteousness", "righteousness", None)],
    "H4194": [("Gen", "01Suh", "01Suh", "01GJe", "the death of the child", "death", None)],
    "H6726": [("Ps", "19zQ2", "19iy2", "19zQ2", "upon Zion, my holy hill", "Zion", None)],
    "H6828": [("Gen", "01Bwp", "01Bwp", "01yNo", "northward and southward", "north", None)],
    "H804": [("Gen", "013Yo", "01ht4", "013Yo", "east of Assyria", "Assyria", None)],
    "H7230": [("Gen", "01eZb", "01imA", "01eZb", "it shall not be counted, for abundance", "abundance", None)],
    "H2451": [("Prov", "20Wkf", "20nAB", "20Wkf", "the beginning of knowledge is wisdom", "wisdom", None)],

    # Batch 19 (2026-08-30): next 20 nouns/adverbs. `edah, yirmeyah,
    # yo'av, shemu'el, and mishkan have no Genesis occurrence, sourced
    # from Exodus/Jeremiah/2 Samuel/1 Samuel.
    "H5712": [("Exod", "021cW", "02ZsF", "02AjK", "the whole congregation of Israel", "congregation", None)],
    "H3414": [("Jer", "24Nvk", "24xeN", "24Nvk", "the words of Jeremiah", "Jeremiah", None)],
    "H4519": [("Gen", "01MXa", "01Z6G", "01MXa", "the name of the firstborn was Manasseh", "Manasseh", None)],
    "H3097": [("2Sam", "10LzS", "10LzS", "10hQD", "and Joab son of Zeruiah", "Joab", None)],
    "H5656": [("Gen", "01nYd", "01nYd", "01yCA", "for the service which you will serve", "service", None)],
    "H1008": [("Gen", "01Uit", "01Uit", "01mrd", "to Bethel", "Bethel", None)],
    "H3162": [("Gen", "01c4r", "01PcK", "01c4r", "to dwell together", "together", None)],
    "H227": [("Gen", "015AY", "015AY", "01HUX", "then people began", "then", None)],
    "H3196": [("Gen", "01Wke", "01sJH", "01Wke", "from the wine", "wine", None)],
    "H3225": [("Gen", "01SiH", "01Pcn", "01SiH", "or if to the right", "right", None)],
    "H5158": [("Gen", "01Y3a", "01Y3a", "01T6R", "in the valley of Gerar", "valley", None)],
    "H5483": [("Gen", "01Jj9", "01Jj9", "01Jj9", "for the horses", "horses", None)],
    "H4605": [("Gen", "01EZX", "01EZX", "01EZX", "from above", "above", None)],
    "H5178": [("Gen", "01rMp", "01USJ", "01rMp", "a forger of bronze", "bronze", None)],
    "H8050": [("1Sam", "09ou4", "09QH2", "09ou4", "his name Samuel", "Samuel", None)],
    "H4908": [("Exod", "02c7F", "02pqU", "02c7F", "the pattern of the tabernacle", "tabernacle", None)],
    "H3678": [("Gen", "01aKZ", "0133u", "01aKZ", "only the throne", "throne", None)],
    "H1568": [("Gen", "01imi", "01ChQ", "01imi", "Mount Gilead", "Gilead", None)],
    "H4557": [("Gen", "018eG", "01125", "018eG", "few in number", "number", None)],
    "H5387": [("Gen", "01F8H", "0133v", "01F8H", "twelve princes", "princes", None)],

    # Batch 20 (2026-08-30): next 20 nouns/pronouns. khomah, khizqiyah,
    # khetsi, tsedeq have no Genesis occurrence, sourced from Joshua,
    # 2 Kings, Exodus, and Psalms.
    "H6153": [("Gen", "01NQN", "01Y3z", "01NQN", "there was evening", "evening", None)],
    "H8121": [("Gen", "011qL", "01EMQ", "011qL", "the sun was going down", "sun", None)],
    "H2346": [("Josh", "066E3", "06Jdo", "066P5", "the wall of the city will fall down", "wall", None)],
    "H6499": [("Gen", "01WzM", "01WzM", "01TYq", "and ten bulls", "bulls", None)],
    "H758": [("Gen", "012Bh", "012Bh", "012Bh", "and Aram", "Aram", None)],
    "H2396": [("2Kgs", "12dor", "12ytA", "12kRt", "Hezekiah his son reigned", "Hezekiah", None)],
    "H2706": [("Gen", "01eWQ", "01B2x", "01ZUN", "for it was a portion for the priests", "portion", None)],
    "H3581": [("Gen", "01wp8", "014Ei", "01wp8", "to yield its strength", "strength", None)],
    "H571": [("Gen", "01T4z", "01T4z", "01T4z", "and his faithfulness", "faithfulness", None)],
    "H6106": [("Gen", "01CmP", "01CmP", "01LY2", "bone of my bones", "bone", None)],
    "H2534": [("Gen", "01dGK", "01rLz", "01dGK", "until your brother's fury turns away", "fury", None)],
    "H2677": [("Exod", "02q8X", "02PrL", "02q8X", "Moses took half of the blood", "half", None)],
    "H6951": [("Gen", "01qjr", "01qjr", "01wRN", "into an assembly of peoples", "assembly", None)],
    "H216": [("Gen", "01W26", "01fpo", "01W26", "let there be light", "light", None)],
    "H587": [("Gen", "01ujL", "01aM6", "01ujL", "we are brothers", "we", None)],
    "H7393": [("Gen", "01juN", "01daH", "01juN", "also chariots", "chariots", None)],
    "H269": [("Gen", "01Ssu", "01Ssu", "01x1x", "and the sister of Tubal-Cain", "sister", None)],
    "H5104": [("Gen", "01zCS", "01zCS", "01LsC", "a river flowed out of Eden", "river", None)],
    "H6529": [("Gen", "01Sov", "01fV3", "01Sov", "fruit tree", "fruit", None)],
    "H6664": [("Ps", "19koG", "19qVd", "19koG", "sacrifices of righteousness", "righteousness", None)],

    # Batch 21 (2026-08-30): next 20 nouns. 8 have no Genesis occurrence,
    # sourced from Joshua, Exodus, 2 Samuel, and 1 Kings.
    "H1060": [("Gen", "01f82", "01f82", "01f82", "his firstborn", "firstborn", None)],
    "H6471": [("Gen", "01ctU", "01ctU", "01ctU", "this time", "time", None)],
    "H8441": [("Gen", "01bMo", "01ZUV", "01bMo", "for it is an abomination to the Egyptians", "abomination", None)],
    "H3956": [("Gen", "01ud1", "019g8", "01ud1", "each according to his language", "language", None)],
    "H4467": [("Gen", "01gCC", "011Xj", "01gCC", "the beginning of his kingdom", "kingdom", None)],
    "H4054": [("Josh", "06qiE", "06qiE", "06qiE", "and their pasturelands", "pasturelands", None)],
    "H8267": [("Exod", "02hnS", "02WW6", "02hnS", "a false witness", "false", None)],
    "H5982": [("Exod", "023fY", "023fY", "024sy", "in a pillar of cloud", "pillar", None)],
    "H3671": [("Gen", "01bYD", "01q1G", "01bYD", "every winged bird", "winged", None)],
    "H5045": [("Gen", "01Ztm", "01Ztm", "01Ztm", "toward the Negev", "Negev", None)],
    "H53": [("2Sam", "10drK", "10F5j", "10drK", "and the third, Absalom", "Absalom", None)],
    "H7676": [("Exod", "028ms", "02GfP", "024aE", "for today is a Sabbath", "Sabbath", None)],
    "H6083": [("Gen", "01ViB", "01ViB", "015Ja", "dust from the ground", "dust", None)],
    "H6862": [("Gen", "01QJA", "01mjE", "01QJA", "who has delivered your enemies into your hand", "enemies", None)],
    "H8111": [("1Kgs", "111QH", "11jWN", "111QH", "the hill of Samaria", "Samaria", None)],
    "H3327": [("Gen", "01qCy", "016iZ", "01qCy", "you shall call his name Isaac", "Isaac", None)],
    "H3532": [("Exod", "02swM", "022y9", "02swM", "from the lambs", "lambs", None)],
    "H5983": [("Gen", "018MU", "019uw", "018MU", "the father of the sons of Ammon", "Ammon", None)],
    "H2708": [("Gen", "01cee", "01cee", "01cee", "my statutes", "statutes", None)],
    "H1116": [("1Kgs", "11NrV", "11oQV", "11NrV", "only at the high places", "high places", None)],

    # Batch 22 (2026-08-30): next 20 nouns. yarov`am, tamid, akh'av have
    # no Genesis occurrence, sourced from 1 Kings/Exodus.
    "H3379": [("1Kgs", "11vo1", "11vo1", "11jQT", "and Jeroboam son of Nebat", "Jeroboam", None)],
    "H4758": [("Gen", "01Kov", "01qVv", "01Kov", "pleasant to the sight", "sight", None)],
    "H8548": [("Exod", "02XTv", "02giK", "02XTv", "before me continually", "continually", None)],
    "H3499": [("Gen", "01dy7", "01dy7", "016Lt", "excelling in dignity", "excelling", None)],
    "H4592": [("Gen", "01a9y", "01a9y", "01am8", "a little water", "little", None)],
    "H7341": [("Gen", "01G8f", "01G8f", "01G8f", "its width", "width", None)],
    "H7458": [("Gen", "01QLb", "01gob", "01QLb", "there was famine in the land", "famine", None)],
    "H123": [("Gen", "01GhY", "01ZHm", "01GhY", "he called his name Edom", "Edom", None)],
    "H5785": [("Gen", "01Atm", "01pjd", "01Atm", "garments of skin", "skin", None)],
    "H6215": [("Gen", "01eJb", "01RA2", "01eJb", "they called his name Esau", "Esau", None)],
    "H7097": [("Gen", "01pMT", "01JEg", "01pMT", "the waters had decreased at the end [of 150 days]", "end", None)],
    "H2543": [("Gen", "01S8J", "01S8J", "01S8J", "and donkeys", "donkeys", None)],
    "H753": [("Gen", "01K8B", "01K8B", "01qTM", "the length of the ark", "length", None)],
    "H3667": [("Gen", "01afe", "01NZQ", "01afe", "the father of Canaan", "Canaan", None)],
    "H8057": [("Gen", "018ii", "018ii", "01WYG", "with joy and songs", "joy", None)],
    "H1847": [("Gen", "01m55", "01qTT", "01m55", "the tree of knowledge", "knowledge", None)],
    "H256": [("1Kgs", "11uo7", "11SGr", "11CVH", "Ahab his son reigned", "Ahab", None)],
    "H6588": [("Gen", "01dE1", "01bU5", "01dE1", "what is my transgression", "transgression", None)],
    "H1616": [("Gen", "01yf4", "01yf4", "01kib", "a sojourner your offspring will be", "sojourner", None)],
    "H2459": [("Gen", "01xjb", "01xjb", "01xjb", "and from their fat", "fat", None)],

    # Batch 23 (2026-08-30): next 20 nouns. 6 have no Genesis occurrence,
    # sourced from Psalms, 1 Kings, 2 Samuel, Leviticus, and Exodus.
    "H3754": [("Gen", "01MnE", "0162B", "01MnE", "he planted a vineyard", "vineyard", None)],
    "H5676": [("Gen", "01fVE", "01fVE", "016aT", "beyond the Jordan", "beyond", None)],
    "H5797": [("Ps", "19UBC", "193zy", "19UBC", "LORD, in your strength", "strength", None)],
    "H2220": [("Gen", "01Vtt", "01Vtt", "01J1d", "the arms of his hands", "arms", None)],
    "H3742": [("Gen", "014Ed", "014Ed", "014Ed", "the cherubim", "cherubim", None)],
    "H4438": [("1Kgs", "11Ci2", "11MRd", "11Ci2", "his kingdom was firmly established", "kingdom", None)],
    "H7892": [("Gen", "01WYG", "01WYG", "01WYG", "and with songs", "songs", None)],
    "H3206": [("Gen", "01UeK", "01UeK", "01CYD", "and a boy for my wound", "boy", None)],
    "H6098": [("2Sam", "10SCB", "10feu", "10SCB", "the counsel of Ahithophel", "counsel", None)],
    "H1817": [("Gen", "01U84", "01U84", "01Jy2", "and he shut the door", "door", None)],
    "H8255": [("Gen", "01RXz", "01PeM", "01RXz", "four hundred shekels of silver", "shekels", None)],
    "H567": [("Gen", "01RyE", "01q1D", "01RyE", "and the Amorite", "Amorite", None)],
    "H6051": [("Gen", "01bVT", "01icY", "01bVT", "I have set [it] in the cloud", "cloud", None)],
    "H6924": [("Gen", "01ZMk", "01ZMk", "01ZMk", "in the east", "east", None)],
    "H8002": [("Lev", "033iR", "03gXh", "033iR", "a sacrifice of peace offerings", "peace offerings", None)],
    "H6285": [("Exod", "0279S", "02vAz", "0279S", "on the four corners", "corners", None)],
    "H1995": [("Gen", "01P34", "01nou", "01xcW", "a father of a multitude of nations", "multitude", None)],
    "H3092": [("1Kgs", "115n2", "115n2", "11WG2", "Jehoshaphat son of Paruah", "Jehoshaphat", None)],
    "H1167": [("Gen", "017h8", "017h8", "01EAv", "allies [in covenant] with Abram", "allies", "lit. \"masters/possessors of a covenant\" -- ba`al's core sense is master/owner; here an idiom for treaty allies")],
    "H1035": [("Gen", "01dR3", "01gt7", "01pmS", "that is Bethlehem", "Bethlehem", None)],
}

# Lemmas Lane said to file away rather than force a single example onto --
# populate as batches turn up a genuinely bad fit (a lemma whose sense is
# too broad/abstract for one occurrence to represent, or whose meaning in
# context resists a clean short English phrase). Empty for batch 1; none of
# the top 20 verbs needed it.
SKIPPED = {
    # "H####": "why -- e.g. 'sense too broad for a single representative phrase'",
}


def load_targets():
    with open(DECK_PATH, encoding="utf-8") as f:
        deck = json.load(f)
    with open(FWEX_PATH, encoding="utf-8") as f:
        fwex_covered = {e["lemma_id"] for e in json.load(f)["entries"]}
    targets = {}
    for e in deck["entries"]:
        if e.get("drillable", True) and e["lemma_id"] not in fwex_covered:
            targets[e["lemma_id"]] = e
    return targets


def main():
    if not os.path.isfile(DECK_PATH):
        sys.exit("data/vocab_deck_600.json not found -- run pipeline/build_vocab_deck.py first")
    if not os.path.isfile(FWEX_PATH):
        sys.exit("data/function_word_examples.json not found -- run pipeline/build_function_word_examples.py first")

    targets = load_targets()

    overlap = set(CURATED) & set(SKIPPED)
    if overlap:
        sys.exit(f"lemma(s) in both CURATED and SKIPPED: {sorted(overlap)}")
    extra_curated = set(CURATED) - set(targets)
    if extra_curated:
        sys.exit(f"CURATED has entries for lemmas outside the target set: {sorted(extra_curated)}")
    extra_skipped = set(SKIPPED) - set(targets)
    if extra_skipped:
        sys.exit(f"SKIPPED has entries for lemmas outside the target set: {sorted(extra_skipped)}")
    for lemma_id, reason in SKIPPED.items():
        if not reason or not reason.strip():
            sys.exit(f"{lemma_id}: SKIPPED entry has no reason")

    book_cache = {}
    entries_out = []
    total_examples = 0

    for lemma_id, picks in CURATED.items():
        entry = targets[lemma_id]
        if not picks:
            sys.exit(f"{lemma_id}: CURATED entry has zero examples")

        examples_out = []
        for book_code, word_id, start_id, end_id, gloss, gloss_highlight, gloss_note in picks:
            tag = f"{lemma_id}/{word_id}"
            if book_code not in book_cache:
                book_cache[book_code] = load_book(book_code)
            verses, word_to_verse = book_cache[book_code]
            vid = word_to_verse.get(word_id)
            if vid is None:
                sys.exit(f"{lemma_id}: word id {word_id!r} not found in {book_code}.xml")
            verse_words = verses[vid]
            target = next(w for w in verse_words if w["id"] == word_id)
            if not matches_lemma(target["lemma"].split("/"), lemma_id):
                sys.exit(
                    f"{lemma_id}: word id {word_id!r} in {vid} has lemma {target['lemma']!r}, "
                    f"which does not resolve to {lemma_id}"
                )

            phrase_words = extract_phrase(verse_words, start_id, end_id, tag)
            phrase_ids = [w["id"] for w in phrase_words]
            if word_id not in phrase_ids:
                sys.exit(f"{tag}: target word id {word_id!r} falls outside its own phrase [{start_id}, {end_id}]")
            target_index = phrase_ids.index(word_id)

            if gloss_highlight not in gloss:
                sys.exit(f"{tag}: gloss_highlight {gloss_highlight!r} is not a substring of gloss {gloss!r}")
            if gloss_note is not None and not gloss_note.strip():
                sys.exit(f"{tag}: gloss_note is present but empty/whitespace")

            surface_form = strip_cantillation(target["text"].replace("/", ""))
            phrase_words_clean = [strip_cantillation(w["text"].replace("/", "")) for w in phrase_words]
            phrase_hebrew = " ".join(phrase_words_clean)
            phrase_translit = " ".join(transliterate(w) for w in phrase_words_clean)

            examples_out.append({
                "ref": vid,
                "surface_form": surface_form,
                "transliteration": transliterate(surface_form),
                "word_id": word_id,
                "phrase_hebrew": phrase_hebrew,
                "phrase_transliteration": phrase_translit,
                "target_index": target_index,
                "gloss": gloss,
                "gloss_highlight": gloss_highlight,
                "gloss_note": gloss_note,
            })
            total_examples += 1

        senses = [s.strip() for s in entry["gloss"].split(",") if s.strip()]
        entries_out.append({
            "lemma_id": lemma_id,
            "citation_form": entry["citation_form"],
            "transliteration": entry["transliteration"],
            "full_gloss": entry["gloss"],
            "sense_count": len(senses),
            "examples": examples_out,
        })

    pending = sorted(set(targets) - set(CURATED) - set(SKIPPED))

    out = {
        "metadata": {
            "source": "build_vocab_examples.py",
            "target_lemma_count": len(targets),
            "curated_count": len(entries_out),
            "skipped": [{"lemma_id": k, "reason": v} for k, v in sorted(SKIPPED.items())],
            "pending_count": len(pending),
        },
        "entries": entries_out,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"vocab_examples.json: {len(entries_out)} lemmas curated, {total_examples} examples, "
          f"{len(SKIPPED)} skipped, {len(pending)} pending of {len(targets)} total targets")


if __name__ == "__main__":
    main()
