# Sample report for `fastdic_plain.sqlite`

Tables: 18 · sampled rows: 10048 of 1133285 · truncated cells (> 5000 chars): 0

## Relationships (declared + detected)

| child | parent | kind | match |
|---|---|---|---|
| english_american_audios.english_word_id | english_words.english_word_id | declared | 100% |
| english_british_audios.english_word_id | english_words.english_word_id | declared | 100% |
| english_categories.english_detail_id | english_details.english_detail_id | declared | 100% |
| english_categories.category | category_names.id | declared | 100% |
| english_details.english_word_id | english_words.english_word_id | declared | 100% |
| english_idioms.english_word_id | english_words.english_word_id | declared | 100% |
| english_idioms.english_idiom_word_id | english_words.english_word_id | declared | 100% |
| english_pos.english_detail_id | english_details.english_detail_id | declared | 100% |
| english_sentences.english_detail_id | english_details.english_detail_id | declared | 100% |
| english_synonyms_antonyms.english_word_id | english_words.english_word_id | declared | 100% |
| english_word_families_words.english_word_family_id | english_word_families.english_word_family_id | declared | 100% |
| english_words.english_word_id_parent | english_words.english_word_id | declared | 100% |
| persian_categories.persian_detail_id | persian_details.persian_detail_id | declared | 100% |
| persian_categories.category | category_names.id | declared | 100% |
| persian_details.persian_word_id | persian_words.persian_word_id | declared | 100% |
| persian_pos.persian_detail_id | persian_details.persian_detail_id | declared | 100% |
| persian_sentences.persian_detail_id | persian_details.persian_detail_id | declared | 100% |
| persian_synonyms_antonyms.persian_word_id | persian_words.persian_word_id | declared | 100% |
| persian_words.persian_word_id_parent | persian_words.persian_word_id | declared | 100% |
| english_categories.sub_category | english_synonyms_antonyms.english_synonyms_antonyms_id | implicit | 100% |
| english_words.simple_past | english_words.english_word_id | implicit | 100% |
| english_words.past_participle | english_words.english_word_id | implicit | 100% |
| english_words.infinitive | english_words.english_word_id | implicit | 100% |
| english_words.plural | english_words.english_word_id | implicit | 100% |
| english_words.present_participle | english_words.english_word_id | implicit | 100% |
| english_words.third_person_singular | english_words.english_word_id | implicit | 100% |
| english_words.comparative | english_words.english_word_id | implicit | 100% |
| english_words.superlative | english_words.english_word_id | implicit | 100% |

## Code / low-cardinality columns (value × rows in FULL db · example ids in sample)

- **english_details.most_common**: `0`×133041 (ids 2,3,5) · `1`×3405 (ids 371,910,4458)
- **english_details.countable_uncountable**: `None`×115621 (ids 2,3,5) · `1`×15784 (ids 7,20,26) · `0`×5041 (ids 9,583,1901)
- **english_details.position**: `0`×112817 (ids 2,3,5) · `1`×8201 (ids 20,2718,3344) · `2`×4402 (ids 3968,4458,6565) · `3`×2716 (ids 7664,10070,12352) · `4`×1845 (ids 56099,101756,104382) · `5`×1321 (ids 101486,106462,106957) · `6`×993 (ids 27241,47976,53724) · `7`×770 (ids 52544,106683,107317) · `8`×595 (ids 55475,101623,106092) · `9`×475 (ids 26220,101624,106580) · `10`×379 (ids 27188,106488,106888) · `11`×313 (ids 105915,106178,106491) · `12`×259 (ids 101960,106875,108358) · `13`×217 (ids 117531,119706,124480) · `14`×185 (ids 106876,118975,119448) · `15`×154 (ids 641,22818,37739) · `16`×131 (ids 44262,117929,129580) · `17`×108 (ids 106206,108692,117713) · `18`×89 (ids 104852,119666,130446) · `19`×71 (ids 26969,131919,132048) · `20`×60 (ids 119660,127613,130344) · `21`×51 (ids 127727,132050,140545) · `22`×44 (ids 15909,131061,131402) · `23`×37 (ids 6677,130347,132052) · `24`×33 (ids 108947,132846,143869) · `25`×30 (ids 127722,135095) · `26`×25 (ids 132737,140382) · `27`×24 (ids 131066,132210,135161) · `28`×21 (ids 119904,130010,135894) · `29`×15 (ids 9347,140134) · `30`×13 (ids 132852,140135,140223) · `31`×10 (ids 132853,140224) · `32`×9 (ids 118155,132854,140383) · `33`×8 (ids 131931,132215,140136) · `34`×6 (ids 131932,144972) · `35`×4 (ids 131410,135182) · `36`×2 (ids 118161,136006) · `49`×1 (ids 132229) · `48`×1 (ids 118158) · `47`×1 (ids 118159) · `46`×1 (ids 118156) · `45`×1 (ids 132228) · `44`×1 (ids 132227) · `43`×1 (ids 132226) · `42`×1 (ids 132225) · `41`×1 (ids 132224) · `40`×1 (ids 132223) · `39`×1 (ids 132222) · `38`×1 (ids 132221) · `37`×1 (ids 132219)
- **english_details.formal_informal**: `None`×133295 (ids 2,3,5) · `0`×2194 (ids 42,7045,53086) · `1`×957 (ids 19631,32190,36436)
- **english_details.british_american**: `None`×133816 (ids 2,3,5) · `0`×1410 (ids 6856,10070,14603) · `1`×1220 (ids 20,980,5382)
- **english_details.cefr**: `None`×123666 (ids 2,3,5) · `B2`×3545 (ids 80,371,427) · `B1`×2480 (ids 26,2718,5107) · `C2`×2293 (ids 5254,20806,22283) · `C1`×2261 (ids 79,6620,6761) · `A2`×1364 (ids 606,980,6286) · `A1`×837 (ids 447,538,7120)
- **english_details.has_image**: `None`×134990 (ids 2,3,5) · `1`×1456 (ids 7,20,1824)
- **english_idioms.position**: `0`×20748 (ids 14,23,27) · `1`×19 (ids 299,4268,4442) · `2`×14 (ids 3931,4273) · `3`×12 (ids 7847,15240) · `8`×8 (ids 4270,9960,15262) · `4`×8 (ids 9951,15242) · `11`×7 (ids 4275,9963) · `10`×7 (ids 3804,9962,15250) · `9`×7 (ids 15248,15263) · `7`×7 (ids 4271,15254) · `6`×7 (ids 3800,9953) · `5`×7 (ids 3799,9952) · `13`×5 (ids 4278,15306) · `12`×5 (ids 3806,15304) · `16`×4 (ids 3813,9994,15315) · `15`×4 (ids 3812,4280,15313) · `14`×4 (ids 9992,15311) · `25`×3 (ids 3827,9839) · `24`×3 (ids 9838,10002) · `23`×3 (ids 4290,10001) · `22`×3 (ids 3824,4288) · `21`×3 (ids 4287,9999) · `20`×3 (ids 3818,9998) · `19`×3 (ids 3817,4285,9997) · `18`×3 (ids 4283,9996) · `17`×3 (ids 4282,9995) · `29`×2 (ids 9843,10007) · `28`×2 (ids 9842,10006) · `27`×2 (ids 9841,10005) · `26`×2 (ids 9840,10004) · `36`×1 (ids 10014) · `35`×1 (ids 10013) · `34`×1 (ids 10012) · `33`×1 (ids 10011) · `32`×1 (ids 10010) · `31`×1 (ids 10009) · `30`×1 (ids 10008)
- **english_pos.pos**: `1`×58922 (ids 7791,7841,18321) · `7`×22267 (ids 6916,35066,54178) · `5`×10604 (ids 22741,98504,102081) · `19`×7418 (ids 166666,167572,171638) · `8`×5603 (ids 18323,21916,22742) · `6`×5243 (ids 145402,145590,195044) · `18`×4581 (ids 166526,167560,168627) · `2`×3402 (ids 76608,80896,89755) · `20`×3315 (ids 161514,173958,195043) · `24`×3006 (ids 221607,222249,229136) · `3`×2803 (ids 27839,28304,31059) · `31`×805 (ids 208733,240145,247672) · `10`×556 (ids 119319,158176,210957) · `30`×380 (ids 231605,233737,254720) · `16`×343 (ids 226372,245535,262970) · `11`×328 (ids 532,73449,126585) · `25`×303 (ids 207748,208043,227458) · `12`×154 (ids 217497,249008,259109) · `9`×127 (ids 163215,210956,246972) · `28`×123 (ids 232924,232973,233012) · `17`×103 (ids 163218,260972) · `32`×72 (ids 253182,267500) · `22`×62 (ids 218754,218791,218826) · `21`×53 (ids 240093,240596) · `27`×31 (ids 229137,229513,247126) · `29`×20 (ids 265552,267170) · `13`×20 (ids 218753,218790,218825) · `34`×17 (ids 233488,233659) · `33`×14 (ids 220581,260823) · `26`×13 (ids 230373,267169) · `23`×10 (ids 239019,249007) · `0`×9 (ids 28501,80897) · `4`×8 (ids 220811,245244) · `14`×2 (ids 136973,267855) · `15`×1 (ids 263797)
- **english_synonyms_antonyms.pos**: `noun`×29959 (ids 3,4,5) · `adjective`×12581 (ids 12,15,25) · `verb`×12007 (ids 1,2,8) · `phrasal verb`×1633 (ids 637,639,4550) · `adverb`×1427 (ids 1367,3006,8986) · `idiom`×267 (ids 52221,54455,54649) · `None`×191 (ids 8848,15685,16834) · `preposition`×71 (ids 538,539,4501) · `abbreviation`×41 (ids 56208,57499,57664) · `symbol`×38 (ids 30960,49456,49856) · `noun, verb`×35 (ids 22242,41556) · `conjunction`×33 (ids 10755,10756,26586) · `adjective, adverb`×33 (ids 38109,51117) · `pronoun`×28 (ids 482,483,4439) · `interjection`×26 (ids 41692,46749,46750) · `phrase`×20 (ids 54594,57341,57967) · `noun, adjective`×18 (ids 13546,19898) · `noun phrase`×16 (ids 56925,57129,57131) · `collocation`×10 (ids 57093,58341) · `verb phrase`×6 (ids 54913,57989) · `adverb, preposition`×5 (ids 9068,17993) · `prefix`×4 (ids 8814,12074,50390) · `transitive verb`×3 (ids 14238,45524,57170) · `determiner`×3 (ids 16661,31650) · `conjuction, preposition`×3 (ids 39202,39203,40518) · `slang`×2 (ids 57193,57265) · `plural noun`×2 (ids 48728,57026) · `article`×2 (ids 27572,27573) · `verb - transitive`×1 (ids 42861) · `preposition, determiner`×1 (ids 42238) · `numeral`×1 (ids 43628) · `noun, interjection`×1 (ids 48134) · `noun, adverb`×1 (ids 15341) · `intransitive verb`×1 (ids 45525) · `exclamation`×1 (ids 57931) · `adverb, pronoun`×1 (ids 30414) · `adjective, preposition`×1 (ids 55420) · `adjective phrase`×1 (ids 57897) · `adjective or adverb`×1 (ids 19551) · `acronym`×1 (ids 46652) · `a person who corrects or changes pi`×1 (ids 40267) · `a bushy tropical American tree rela`×1 (ids 25596) · `Phrasal varb`×1 (ids 58259) · `Noun`×1 (ids 58310) · `BBC`×1 (ids 44193) · `Adverb`×1 (ids 58039) · `Adjective`×1 (ids 58263)
- **english_synonyms_antonyms.position**: `0`×58352 (ids 1,2,3) · `1`×75 (ids 2458,4588,7979) · `2`×28 (ids 2459,7980,14867) · `3`×13 (ids 12549,16216,58325) · `4`×7 (ids 19655,58331) · `5`×3 (ids 14153,19656) · `10`×1 (ids 19661) · `9`×1 (ids 19660) · `8`×1 (ids 19659) · `7`×1 (ids 19658) · `6`×1 (ids 19657)
- **english_word_families_words.pos**: `1`×2269 (ids 1,4,5) · `7`×1579 (ids 2,6,18) · `5`×824 (ids 3,881,1660) · `8`×732 (ids 16,21,1700) · `6`×118 (ids 1519,1680)
- **persian_details.position**: `0`×109280 (ids 774,775,776) · `1`×6002 (ids 3372,12130,12228) · `2`×1170 (ids 2007,14504,17596) · `3`×404 (ids 13988,34887,48422) · `4`×209 (ids 25386,34875,34888) · `5`×104 (ids 131104,131923,132860) · `6`×51 (ids 2242,131272,131414) · `7`×38 (ids 50941,130488,131257) · `8`×25 (ids 47619,106718,130489) · `9`×20 (ids 106719,131259,131624) · `10`×15 (ids 2263,47621,130976) · `11`×12 (ids 78515,131419,132696) · `12`×10 (ids 131179,131420,132697) · `13`×6 (ids 47783,132698) · `14`×5 (ids 131629,132699) · `15`×4 (ids 131174,131423) · `18`×3 (ids 131177,131426) · `17`×3 (ids 131176,131425) · `16`×3 (ids 131175,131631) · `22`×2 (ids 131182,131637) · `21`×2 (ids 131181,131636) · `20`×2 (ids 131180,131635) · `19`×2 (ids 131178,131634)
- **persian_details.has_image**: `None`×116410 (ids 774,775,776) · `1`×962 (ids 822,1830,2839)
- **persian_pos.pos**: `1`×9066 (ids 868,1559,1705) · `2`×2789 (ids 965,2918,3209) · `5`×735 (ids 10056,10392,10694) · `4`×668 (ids 6928,10693,10695) · `8`×574 (ids 7970,13101,13954) · `3`×470 (ids 3475,6331,13884) · `21`×166 (ids 15070,18520) · `7`×122 (ids 11003,11004,15895) · `12`×70 (ids 8872,8876,19036) · `23`×47 (ids 4839,14236) · `16`×44 (ids 4008,7180,7674) · `6`×40 (ids 10074,10091,11565) · `22`×30 (ids 8140,19033) · `30`×25 (ids 12173,13259,19012) · `18`×24 (ids 6994,9174) · `13`×21 (ids 10098,18323,18324) · `29`×16 (ids 10886,13675) · `24`×14 (ids 8744,18531) · `20`×12 (ids 5095,12172) · `15`×10 (ids 9215,19702) · `31`×8 (ids 15847,18225) · `27`×4 (ids 7805,15241) · `28`×2 (ids 10527,12685) · `11`×1 (ids 46)
- **persian_sentences.position**: `0`×25385 (ids 611,615,617) · `1`×2991 (ids 311,4793,4844) · `2`×770 (ids 122,1021,6047) · `3`×271 (ids 831,1056,6048) · `4`×98 (ids 309,6254,7044) · `5`×49 (ids 834,7041,21770) · `6`×31 (ids 307,2798,21636) · `7`×19 (ids 133,2799,22732) · `8`×11 (ids 300,487,23131) · `9`×9 (ids 302,22928) · `10`×7 (ids 303,4988,22931) · `11`×6 (ids 490,22736) · `12`×5 (ids 104,305) · `13`×4 (ids 105,492) · `15`×2 (ids 314,315) · `14`×2 (ids 299,312) · `18`×1 (ids 320) · `17`×1 (ids 319) · `16`×1 (ids 317)
- **persian_synonyms_antonyms.position**: `0`×26699 (ids 1,2,3) · `1`×8 (ids 14225,16296) · `2`×7 (ids 15483,20324,22664) · `6`×3 (ids 23652,24763,26119) · `4`×3 (ids 20847,23021,24868) · `3`×3 (ids 23268,23385,24595) · `8`×2 (ids 25085,26528) · `11`×1 (ids 26697) · `10`×1 (ids 26665) · `9`×1 (ids 26613) · `7`×1 (ids 26386) · `5`×1 (ids 25684)
- **persian_words.canonical**: `None`×108070 (ids 774,775,776) · ``×658 (ids 783,1830,3431) · `https://fastdic.com/number/900`×1 (ids 29591) · `https://fastdic.com/number/90`×1 (ids 29628) · `https://fastdic.com/number/80`×1 (ids 30959) · `https://fastdic.com/number/8`×1 (ids 30958) · `https://fastdic.com/number/700`×1 (ids 30989) · `https://fastdic.com/number/70`×1 (ids 126670) · `https://fastdic.com/number/7`×1 (ids 31002) · `https://fastdic.com/number/600`×1 (ids 17166) · `https://fastdic.com/number/60`×1 (ids 17145) · `https://fastdic.com/number/500`×1 (ids 4848) · `https://fastdic.com/number/50`×1 (ids 5448) · `https://fastdic.com/number/5`×1 (ids 5441) · `https://fastdic.com/number/400`×1 (ids 8581) · `https://fastdic.com/number/40`×1 (ids 8682) · `https://fastdic.com/number/4`×1 (ids 8558) · `https://fastdic.com/number/300`×1 (ids 16805) · `https://fastdic.com/number/30`×1 (ids 16679) · `https://fastdic.com/number/3`×1 (ids 16203) · `https://fastdic.com/number/200`×1 (ids 12893) · `https://fastdic.com/number/20`×1 (ids 4223) · `https://fastdic.com/number/2`×1 (ids 12089) · `https://fastdic.com/number/19`×1 (ids 29660) · `https://fastdic.com/number/18`×1 (ids 30837) · `https://fastdic.com/number/17`×1 (ids 30910) · `https://fastdic.com/number/16`×1 (ids 17006) · `https://fastdic.com/number/15`×1 (ids 4851) · `https://fastdic.com/number/14`×1 (ids 8611) · `https://fastdic.com/number/13`×1 (ids 16797) · `https://fastdic.com/number/12`×1 (ids 12265) · `https://fastdic.com/number/11`×1 (ids 31631) · `https://fastdic.com/number/10000000`×1 (ids 80513) · `https://fastdic.com/number/1000000`×1 (ids 128721) · `https://fastdic.com/number/10000`×1 (ids 12851) · `https://fastdic.com/number/1000`×1 (ids 30789) · `https://fastdic.com/number/100`×1 (ids 18255) · `https://fastdic.com/number/10`×1 (ids 12887) · `https://fastdic.com/number/1`×1 (ids 31494)

## Tables

### category_names  — 82 rows in full db, 82 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| id 🔑 | INTEGER | 0 | 0 | 82 | 1 | 82 | 2 |
| persian_category_name | varchar(255) | 0 | 0 | 82 | آب‌و‌هوا | ۵۰۴ واژه | 20 |
| english_category_name | varchar(255) | 0 | 0 | 82 | 504 Absolutely Essential … | ‪Bodybuilding‬ | 40 |
| is_hidden | boolean | 0 | 0 | 2 | 0 | 1 | 1 |
| is_my_words | boolean | 0 | 0 | 2 | 0 | 1 | 1 |

Example values (non-empty, from the sample):

- `id`: 1 ⏐ 2 ⏐ 3
- `persian_category_name`: گیاه‌شناسی ⏐ جانورشناسی ⏐ شیمی
- `english_category_name`: Botany ⏐ Zoology ⏐ Chemistry
- `is_hidden`: 0 ⏐ 1
- `is_my_words`: 1 ⏐ 0

### english_word_families  — 1044 rows in full db, 32 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_word_family_id 🔑 | INTEGER | 0 | 0 | 1044 | 1 | 1044 | 4 |

Example values (non-empty, from the sample):

- `english_word_family_id`: 1 ⏐ 2 ⏐ 3

### english_american_audios  — 83820 rows in full db, 768 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_american_audio_id 🔑 | INTEGER | 0 | 0 | 83820 | 2 | 91707 | 5 |
| filename | varchar(70) | 18483 | 0 | 64710 | 100000 | zoology | 27 |
| phonetic | varchar(255) | 16280 | 1 | 65017 |  | θʌɡ | 64 |
| english_word_id | INTEGER | 0 | 0 | 82502 | 2 | 146365 | 6 |

Example values (non-empty, from the sample):

- `english_american_audio_id`: 2 ⏐ 3 ⏐ 4
- `filename`: propagate ⏐ EUS25995 ⏐ EUS01923
- `phonetic`: ˈprɑːpəɡeɪt ⏐ əˈrɪə ⏐ blɑːˈkeɪd
- `english_word_id`: 2 ⏐ 3 ⏐ 5

### english_british_audios  — 83797 rows in full db, 768 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_british_audio_id 🔑 | INTEGER | 0 | 0 | 83797 | 2 | 91988 | 5 |
| filename | varchar(70) | 18511 | 0 | 64684 | 100000 | ukzzzze108 | 23 |
| phonetic | varchar(255) | 16274 | 1 | 64820 |  | θʌɡ | 58 |
| english_word_id | INTEGER | 0 | 0 | 82496 | 2 | 146365 | 6 |

Example values (non-empty, from the sample):

- `english_british_audio_id`: 2 ⏐ 3 ⏐ 4
- `filename`: UKPROOF008 ⏐ EPD26460 ⏐ EPD01968
- `phonetic`: ˈprɒpəɡeɪt ⏐ əˈrɪə ⏐ blɒˈkeɪd
- `english_word_id`: 2 ⏐ 3 ⏐ 5

### english_categories  — 33879 rows in full db, 295 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_category_id 🔑 | INTEGER | 0 | 0 | 33879 | 2 | 47894 | 5 |
| category | bigint | 0 | 0 | 81 | 1 | 81 | 2 |
| english_detail_id | INTEGER | 0 | 0 | 28374 | 7 | 147692 | 6 |
| sub_category | INTEGER | 21341 | 0 | 101 | 1 | 101 | 3 |

Example values (non-empty, from the sample):

- `english_category_id`: 2 ⏐ 3 ⏐ 4
- `category`: 1 ⏐ 2 ⏐ 3
- `english_detail_id`: 7 ⏐ 20 ⏐ 526
- `sub_category`: 1 ⏐ 2 ⏐ 3

### english_details  — 136446 rows in full db, 1456 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_detail_id 🔑 | INTEGER | 0 | 0 | 136446 | 2 | 147693 | 6 |
| persian_meaning | TEXT | 0 | 0 | 132848 |  d  Ph مسکوک مسی آلمانی… | ‫‫رابطه‌ی متقابل‬ | 295 |
| most_common | boolean | 0 | 0 | 2 | 0 | 1 | 1 |
| countable_uncountable | boolean | 115621 | 0 | 2 | 0 | 1 | 1 |
| english_word_id | INTEGER | 0 | 0 | 102561 | 2 | 146365 | 6 |
| position | INTEGER | 0 | 0 | 50 | 0 | 49 | 2 |
| formal_informal | boolean | 133295 | 0 | 2 | 0 | 1 | 1 |
| british_american | boolean | 133816 | 0 | 2 | 0 | 1 | 1 |
| cefr | varchar(2) | 123666 | 0 | 6 | A1 | C2 | 2 |
| has_image | INTEGER | 134990 | 0 | 1 | 1 | 1 | 1 |
| description_html | TEXT | 134564 | 1078 | 775 |  | <p>گذشته‌ی ساده و شکل سوم… | 318 |

Example values (non-empty, from the sample):

- `english_detail_id`: 2 ⏐ 18637 ⏐ 3
- `persian_meaning`: گستردن، (به‌وسیله‌ی تولید مثل) تکثیر کردن، زیاد کردن، پروردن، قلمه زدن، منتشرکردن، انتشار دادن ⏐ سینمای غیرمتحرک، چراغ عکس، شهر فرنگ ⏐ به عقب، در پشت، بدهی پس‌افتاده، پس افت
- `most_common`: 0 ⏐ 1
- `countable_uncountable`: 1 ⏐ 0
- `english_word_id`: 2 ⏐ 3 ⏐ 5
- `position`: 0 ⏐ 1 ⏐ 15
- `formal_informal`: 0 ⏐ 1
- `british_american`: 1 ⏐ 0
- `cefr`: A1 ⏐ A2 ⏐ B1
- `has_image`: 1
- `description_html`: <p>همچنین می‌توان از <a href="" class="js-word-link bank-account'" rel="noopener noreferrer">bank ac… ⏐ <p>ترکیب کلمه‌های <a href="" class="js-word-link internal'" rel="noopener noreferrer">internal</a> و… ⏐ <p>شکل جمع این کلمه در انگلیسی بریتانیایی: turves</p>

### english_idioms  — 20915 rows in full db, 597 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_idiom_id 🔑 | INTEGER | 0 | 0 | 20915 | 1 | 21976 | 5 |
| english_idiom_word_id | INTEGER | 0 | 0 | 11086 | 371 | 145574 | 6 |
| position | INTEGER | 0 | 0 | 37 | 0 | 36 | 2 |
| english_word_id | INTEGER | 0 | 0 | 3760 | 6 | 146315 | 6 |

Example values (non-empty, from the sample):

- `english_idiom_id`: 8117 ⏐ 4622 ⏐ 7484
- `english_idiom_word_id`: 371 ⏐ 427 ⏐ 699
- `position`: 0 ⏐ 1 ⏐ 5
- `english_word_id`: 6 ⏐ 7 ⏐ 100

### english_pos  — 130718 rows in full db, 370 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_pos_id 🔑 | INTEGER | 0 | 0 | 130718 | 16 | 272540 | 6 |
| pos | INTEGER | 0 | 0 | 35 | 0 | 34 | 2 |
| english_detail_id | INTEGER | 0 | 0 | 113627 | 2 | 147693 | 6 |

Example values (non-empty, from the sample):

- `english_pos_id`: 139763 ⏐ 139764 ⏐ 147899
- `pos`: 11 ⏐ 7 ⏐ 1
- `english_detail_id`: 2 ⏐ 3 ⏐ 5

### english_sentences  — 135208 rows in full db, 469 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_sentence_id 🔑 | INTEGER | 0 | 0 | 135208 | 7 | 152259 | 6 |
| english_sentence | TEXT | 0 | 0 | 134892 |     Every possible pressu… | ‪When we are driving, we … | 250 |
| persian_sentence | TEXT | 0 | 2 | 134385 |  | ﻿من معمولاً زیر لباس‌های … | 266 |
| english_detail_id | INTEGER | 0 | 0 | 55503 | 6 | 147693 | 6 |
| position | INTEGER | 0 | 0 | 71 | 0 | 70 | 2 |

Example values (non-empty, from the sample):

- `english_sentence_id`: 9031 ⏐ 9032 ⏐ 88875
- `english_sentence`: The hot spring is one of the popular tourist attractions in this region. ⏐ Bathing in a mineral spring can help relieve joint pain. ⏐ spruce somebody up
- `persian_sentence`: چشمه‌ی آب گرم یکی از جاذبه‌های گردشگری محبوب در این منطقه است. ⏐ حمام کردن در چشمه‌ی آب معدنی می‌تواند به کاهش درد مفاصل کمک کند. ⏐ (Verb - transitive) خود را آراستن، خود را آراسته کردن، شیک کردن
- `english_detail_id`: 6 ⏐ 7 ⏐ 9
- `position`: 0 ⏐ 1 ⏐ 10

### english_synonyms_antonyms  — 58483 rows in full db, 961 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_synonyms_antonyms_id 🔑 | INTEGER | 0 | 0 | 58483 | 1 | 58483 | 5 |
| english_word_id | INTEGER | 0 | 0 | 38986 | 2 | 146365 | 6 |
| definitions | TEXT | 1420 | 0 | 45827 | (19th century) a man's hi… | ‪to successfully manage a… | 1432 |
| synonyms | TEXT | 3517 | 0 | 54530 | 10, x, ten-spot, tenner, … | österreich, republic-of-a… | 1504 |
| antonyms | TEXT | 42193 | 0 | 13821 | Pull-down | zygomorphic | 464 |
| pos | varchar(35) | 191 | 0 | 46 | Adjective | verb phrase | 35 |
| position | INTEGER | 0 | 0 | 11 | 0 | 10 | 2 |

Example values (non-empty, from the sample):

- `english_synonyms_antonyms_id`: 1 ⏐ 2 ⏐ 3
- `english_word_id`: 2 ⏐ 6 ⏐ 7
- `definitions`: breed, reproduce ⏐ spread, make known ⏐ barrier
- `synonyms`: reproduce, produce, generate, procreate, grow, multiply, increase, raise, bear, father, mother, bege… ⏐ publish, distribute, circulate, publicize, broadcast, disseminate, transmit, diffuse, scatter, dispe… ⏐ obstacle, barrier, obstruction, impediment, restriction, stop, wall, roadblock, hindrance, barricade…
- `antonyms`: kill, destroy ⏐ hide, conceal ⏐ opening
- `pos`: verb ⏐ noun ⏐ adjective
- `position`: 0 ⏐ 1 ⏐ 2

### english_word_families_words  — 5522 rows in full db, 82 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_word_family_words_id 🔑 | INTEGER | 0 | 0 | 5522 | 1 | 5910 | 4 |
| english_word_family_id | INTEGER | 0 | 0 | 1044 | 1 | 1044 | 4 |
| pos | INTEGER | 0 | 0 | 5 | 1 | 8 | 1 |
| word | varchar(255) | 0 | 0 | 4804 | abandon | zoroastrianism | 20 |

Example values (non-empty, from the sample):

- `english_word_family_words_id`: 1 ⏐ 2 ⏐ 3
- `english_word_family_id`: 1 ⏐ 2 ⏐ 3
- `pos`: 1 ⏐ 7 ⏐ 5
- `word`: abandonment ⏐ abandoned ⏐ abandon

### english_words  — 134784 rows in full db, 2376 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| english_word_id 🔑 | INTEGER | 0 | 0 | 134784 | 2 | 146372 | 6 |
| english_word | varchar(100) | 0 | 0 | 134784 | 'cello | ‪documentary credit‬ | 69 |
| simple_past | INTEGER | 128589 | 0 | 5189 | 86 | 146369 | 6 |
| past_participle | INTEGER | 128626 | 0 | 5129 | 229 | 146369 | 6 |
| infinitive | INTEGER | 134636 | 0 | 114 | 1474 | 144672 | 6 |
| plural | INTEGER | 124126 | 0 | 10640 | 1276 | 146372 | 6 |
| present_participle | INTEGER | 128678 | 0 | 5136 | 80 | 146368 | 6 |
| third_person_singular | INTEGER | 128025 | 0 | 5079 | 1844 | 146367 | 6 |
| comparative | INTEGER | 131973 | 0 | 2785 | 1513 | 146355 | 6 |
| superlative | INTEGER | 131932 | 0 | 2788 | 258 | 146354 | 6 |
| canonical | varchar(255) | 134784 | 0 | 0 | None | None | 0 |
| word_description_html | TEXT | 129063 | 0 | 5716 | <p> در معنای اول LLM مخفف… | <p>گذشته‌ی ساده و شکل سوم… | 1145 |
| english_word_id_parent | INTEGER | 102561 | 0 | 18853 | 2 | 146365 | 6 |

Example values (non-empty, from the sample):

- `english_word_id`: 2 ⏐ 3 ⏐ 5
- `english_word`: (all) plain sailing ⏐ (as) fresh as a daisy ⏐ (in) the worst way
- `simple_past`: 127597 ⏐ 127598 ⏐ 127599
- `past_participle`: 127597 ⏐ 127598 ⏐ 127599
- `infinitive`: 21810 ⏐ 17533 ⏐ 144464
- `plural`: 57499 ⏐ 108359 ⏐ 108360
- `present_participle`: 116363 ⏐ 116364 ⏐ 116365
- `third_person_singular`: 119881 ⏐ 108359 ⏐ 108361
- `comparative`: 122090 ⏐ 54140 ⏐ 131994
- `superlative`: 124818 ⏐ 124842 ⏐ 124851
- `canonical`: *(no non-empty value)*
- `word_description_html`: <p>همچنین در حالت گذشته می‌توان از sunburnt به‌جای sunburned استفاده کرد.</p> ⏐ <p>همچنین می‌توان از alpha geminorum به‌ جای castor استفاده کرد.</p> ⏐ <p>همچنین می‌توان از hopple به‌ جای hobble استفاده کرد.</p>
- `english_word_id_parent`: 2 ⏐ 6 ⏐ 7

### persian_categories  — 11099 rows in full db, 185 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_category_id 🔑 | INTEGER | 0 | 0 | 11099 | 1 | 13466 | 5 |
| category | bigint | 0 | 0 | 67 | 1 | 80 | 2 |
| persian_detail_id | INTEGER | 0 | 0 | 10645 | 822 | 132912 | 6 |

Example values (non-empty, from the sample):

- `persian_category_id`: 1 ⏐ 19 ⏐ 25
- `category`: 1 ⏐ 2 ⏐ 3
- `persian_detail_id`: 822 ⏐ 1560 ⏐ 1830

### persian_details  — 117372 rows in full db, 525 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_detail_id 🔑 | INTEGER | 0 | 0 | 117372 | 774 | 132912 | 6 |
| english_meaning | TEXT | 0 | 0 | 73582 |  (in compounds) to end, t… | ‪sharpness, acuteness‬ | 665 |
| persian_phonetic | varchar(100) | 87887 | 2031 | 26419 |  | õzhandan | 49 |
| persian_meaning | TEXT | 94546 | 2078 | 15132 |  | ‫فتنه‌گر | 153 |
| persian_word_id | INTEGER | 0 | 0 | 107912 | 774 | 130927 | 6 |
| position | INTEGER | 0 | 0 | 23 | 0 | 22 | 2 |
| has_image | INTEGER | 116410 | 0 | 1 | 1 | 1 | 1 |

Example values (non-empty, from the sample):

- `persian_detail_id`: 774 ⏐ 130161 ⏐ 775
- `english_meaning`: barber, beautician, hairdresser, hair-stylist, coiffeur, cosmetologist ⏐ actress, actor, movie star, performer ⏐ flour, farina, powder, dust
- `persian_phonetic`: aaraayeshgar1 ⏐ aartist ⏐ aard
- `persian_meaning`: کسی که دیگران را آرایش می‌کند ⏐ بازیگر ⏐ ماده‌ی پودرمانندی است که از دانه‌ی غلات یا سایر مواد نشاسته‌ای به دست می‌آید
- `persian_word_id`: 774 ⏐ 775 ⏐ 776
- `position`: 0 ⏐ 2 ⏐ 6
- `has_image`: 1

### persian_pos  — 14958 rows in full db, 185 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_pos_id 🔑 | INTEGER | 0 | 0 | 14958 | 2 | 19812 | 5 |
| pos | INTEGER | 0 | 0 | 24 | 1 | 31 | 2 |
| persian_detail_id | INTEGER | 0 | 0 | 14334 | 774 | 132912 | 6 |

Example values (non-empty, from the sample):

- `persian_pos_id`: 5412 ⏐ 5370 ⏐ 9145
- `pos`: 11 ⏐ 1 ⏐ 2
- `persian_detail_id`: 774 ⏐ 775 ⏐ 776

### persian_sentences  — 29663 rows in full db, 333 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_sentence_id 🔑 | INTEGER | 0 | 0 | 29663 | 6 | 30157 | 5 |
| persian_sentence | TEXT | 0 | 0 | 28838 | "Ray" مخفف "Raymound" است… |  باد قریب‌الوقوع است. | 201 |
| english_sentence | TEXT | 0 | 0 | 28595 |   I’m trying out a new co… | ‪Zeynab lost her phone.‬ | 244 |
| persian_detail_id | INTEGER | 0 | 0 | 13663 | 774 | 132912 | 6 |
| position | INTEGER | 0 | 0 | 19 | 0 | 18 | 2 |

Example values (non-empty, from the sample):

- `persian_sentence_id`: 7278 ⏐ 7279 ⏐ 7211
- `persian_sentence`: از شیر گرفتن ⏐ بطری شیر کودک ⏐ یک جفت کفش تنگ
- `english_sentence`: to wean ⏐ nursing bottle ⏐ a pair of tight shoes
- `persian_detail_id`: 774 ⏐ 775 ⏐ 776
- `position`: 12 ⏐ 13 ⏐ 2

### persian_synonyms_antonyms  — 26730 rows in full db, 167 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_synonyms_antonyms_id 🔑 | INTEGER | 0 | 0 | 26730 | 1 | 26730 | 5 |
| persian_word_id | INTEGER | 0 | 0 | 14189 | 774 | 130828 | 6 |
| synonym_antonym | TEXT | 0 | 0 | 25524 | s | یگانگی ≠ پراکندگی، کثرت | 264 |
| position | INTEGER | 0 | 0 | 12 | 0 | 11 | 2 |

Example values (non-empty, from the sample):

- `persian_synonyms_antonyms_id`: 1 ⏐ 14174 ⏐ 20095
- `persian_word_id`: 774 ⏐ 775 ⏐ 777
- `synonym_antonym`: آراینده ⏐ آکتور، بازیگر، ستاره، هنرپیشه، هنرمند ⏐ پیرایشگاه، حلاق، سلمانی
- `position`: 0 ⏐ 1 ⏐ 2

### persian_words  — 108765 rows in full db, 397 in sample

| column | type | nulls | empty | distinct | min | max | max len |
|---|---|---|---|---|---|---|---|
| persian_word_id 🔑 | INTEGER | 0 | 0 | 108765 | 774 | 130930 | 6 |
| persian_word | varchar(255) | 0 | 0 | 108765 | -کوب | ییلاقی | 28 |
| word_in_number | varchar(255) | 0 | 0 | 107813 | 10 | 876585 | 56 |
| canonical | varchar(255) | 108070 | 658 | 38 |  | https://fastdic.com/numbe… | 35 |
| word_description_html | TEXT | 107015 | 940 | 811 |  | <p>پایتخت:‌Pretoria (admi… | 211 |
| persian_word_id_parent | INTEGER | 107912 | 0 | 703 | 876 | 130918 | 6 |

Example values (non-empty, from the sample):

- `persian_word_id`: 774 ⏐ 775 ⏐ 776
- `persian_word`: آب ⏐ آب رسان ⏐ آب عقب زده شده در اثر جزرومد
- `word_in_number`: 10101343891585102925 ⏐ 1010401085896380654325 ⏐ 10106710698963432980891310891943898389192910858940851029
- `canonical`: https://fastdic.com/number/20 ⏐ https://fastdic.com/number/500 ⏐ https://fastdic.com/number/15
- `word_description_html`: <p>پایتخت:‌ Buenos Aires</p><p>ملیت: Argentinian</p><p>مخفف: AR</p> ⏐ <p>همچنین می‌توان از <strong>پسته‌شام</strong>، <strong>بادام‌کوهی</strong> و <strong>بادام‌خاکی</st… ⏐ <p>همچنین می‌توان از <strong>برانی</strong> به‌جای <strong>بورانی</strong> استفاده کرد.</p>
- `persian_word_id_parent`: 1830 ⏐ 29130 ⏐ 60682
