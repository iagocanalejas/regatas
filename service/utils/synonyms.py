from typing import List, Set, Iterable

from simplemma import text_lemmatizer
from unidecode import unidecode

from ai_django.ai_core.utils.strings import remove_symbols, remove_conjunctions

FEMALE = 'FEMENINA'
FLAG = 'BANDERA'
GRAND_PRIX = 'GRAN PREMIO'
TOWN = 'AYUNTAMIENTO'
TIME_TRIAL = 'CONTRARRELOJ'
BOAT = 'TRAINERA'
RACE = 'REGATA'
DEPUTATION = 'DIPUTACIÓN'
CLASSIFICATION = 'CLASIFICATORIA'

__synonyms = {
    FEMALE: ['FEMENINA', 'FEMININA', 'FEMINAS', 'EMAKUMEEN', 'EMAKUMEAK', 'NESKEN', 'NESKA', 'EMAKUMEZKOEN'],
    FLAG: ['BANDERA', 'BANDEIRA', 'IKURRIÑA'],
    GRAND_PRIX: ['GRAN PREMIO', 'SARI NAGUSIA'],
    TOWN: [
        'AYUNTAMIENTO', 'CONCELLO', 'CONCEJO', 'UDALETXEA', 'UDALA', 'VILA', 'VILLA', 'CIUDAD', 'HIRIA', 'HIRIKO',
        'CIDADE'
    ],
    TIME_TRIAL: ['CONTRARRELOJ', 'CONTRARRELOXO', 'ERLOJUPEKOA', 'ERLOJU KONTRA', 'CONTRA RELOJ'],
    BOAT: ['TRAINERA', 'TRAINERAS', 'TRAINERU', 'TRAIÑA', 'TRAIÑAS', 'TRAIÑEIRA', 'TRAIÑEIRAS'],
    RACE: ['REGATA', 'REGATAS', 'ESTROPADA', 'ESTROPADAK'],
    DEPUTATION: ['DEPUTACIÓN', 'DIPUTACIÓN'],
    CLASSIFICATION: ['SAILKAPEN OROKORRA', 'CLASIFICACION GENERAL', 'ELIMINATORIA'],
}

__expansions = [
    ['trofeo', 'bandera'],
    ['trainera', None],
]


# noinspection PyPep8Naming
def FEMALE_SYNONYMS() -> List[str]:
    return __synonyms[FEMALE]


# noinspection PyPep8Naming
def FLAG_SYNONYMS() -> List[str]:
    return __synonyms[FLAG]


# noinspection PyPep8Naming
def GRAND_PRIX_SYNONYMS() -> List[str]:
    return __synonyms[GRAND_PRIX]


# noinspection PyPep8Naming
def TOWN_SYNONYMS() -> List[str]:
    return __synonyms[TOWN]


# noinspection PyPep8Naming
def TIME_TRIAL_SYNONYMS() -> List[str]:
    return __synonyms[TIME_TRIAL]


# noinspection PyPep8Naming
def CLASSIFICATION_SYNONYMS() -> List[str]:
    return __synonyms[CLASSIFICATION]


def normalize_synonyms(phrase: str) -> str:
    for k, v in __synonyms.items():
        for w in v:
            if ' ' in w:
                phrase = phrase.replace(w, k).replace(unidecode(w), unidecode(k))
            else:
                phrase = ' '.join([e if e != w and unidecode(e) != unidecode(w) else k for e in phrase.split()])
    return phrase


def lemmatize(phrase: str) -> Set[str]:
    name = normalize_synonyms(phrase)
    name = remove_symbols(unidecode(remove_conjunctions(name)))
    return set(text_lemmatizer(name, lang='es'))


def expand_lemmas(lemmas: Iterable[str]) -> List[List[str]]:
    """
    Expand the lemmas to use in search queries
    Ex:
        [trofeo] -> [[trofeo], [bandera]]
    """
    expanded = [lemmas]
    for group in __expansions:
        if not any(w in lemmas for w in group):
            continue

        # remove the words for all the expanded
        expanded = [[w for w in le if w not in group] for le in expanded]

        # add new expansions
        new_expanded = []
        for le in expanded:
            for w in group:
                nle = le.copy()
                if w:  # this allows to remove a lemma in a new set
                    nle.append(w)
                new_expanded.append(nle)
        expanded = new_expanded
    return expanded
