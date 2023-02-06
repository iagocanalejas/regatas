import logging

from django.db.models import Q
from django.db.models.functions import Length
from unidecode import unidecode

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_parenthesis
from apps.entities.models import EntityTitle, Entity
from utils.choices import ENTITY_CLUB

logger = logging.getLogger(__name__)

# list of normalizations to specific to be implemented
__ENTITY_TITLES = ['CR', 'SD', 'SDR', 'CM', 'CR', 'AD', 'CC', 'CDM', 'CCD', 'CRN', 'FEM', 'B']
__NORMALIZED_ENTITIES = {
    'CABO DA CRUZ': ['CABO DE CRUZ', 'CABO'],
    'ARES': ['DE ARES'],
    'CESANTES': ['CESANTES REMO - RODAVIGO'],
    'FEDERACION GALEGA DE REMO': ['LGT - FEGR'],
    'PERILLO': ['SALGADO PERILLO'],
    'LIGA GALEGA DE TRAIÑAS': ['LIGA GALEGA TRAIÑEIRAS', 'LIGA GALEGA TRAINEIRAS', 'LGT'],
    'BUEU': ['BUEU TECCARSA'],
    'ESTEIRANA': ['ESTEIRANA REMO'],
    'A CABANA': ['A CABANA FERROL'],
    'RIVEIRA': ['DE RIVEIRA'],
    'ZARAUTZ': ['ZARAUTZ GESALAGA-OKELAN', 'ZARAUTZ INMOB. ORIO'],
    'PASAI DONIBANE KOXTAPE': ['P.DONIBANE IBERDROLA'],
    'HONDARRIBIA': ['HONADRRIBIA', 'HONDARRBIA'],
    'ONDARROA': ['OMDARROA'],
    'ILLUMBE': ['ILLUNBE'],
    'PORTUGALETE': ['POTUGALETE'],
    'GETXO': ['GETRXO'],
    'DONOSTIARRA': ['DNOSTIARRA'],
}
__LEAGUES_MAP = {
    'LIGA GALEGA DE TRAIÑAS': ['LGT'],
    'LIGA GALEGA DE TRAIÑAS A': ['LIGA A'],
    'LIGA GALEGA DE TRAIÑAS B': ['LIGA B'],
    'LIGA GALEGA DE TRAIÑAS FEMENINA': ['LIGA FEM', 'LIGA F'],
    'ASOCIACIÓN DE CLUBES DE TRAINERAS': ['ACT'],
}


def normalize_league_name(name: str) -> str:
    for k, v in __LEAGUES_MAP.items():
        if name in v:
            name = k
            break
    return name


def normalize_club_name(name: str) -> str:
    name = whitespaces_clean(remove_parenthesis(name.upper()))
    name = remove_club_title(name)
    name = remove_club_sponsor(name)

    # specific club normalizations
    for k, v in __NORMALIZED_ENTITIES.items():
        if name in v or any(part in name for part in v):
            name = k
            break

    return whitespaces_clean(name)


def remove_club_title(name: str) -> str:
    name = ' '.join(w for w in name.split() if w not in __ENTITY_TITLES)
    for title in EntityTitle.objects.all().order_by(Length('name').desc()).values_list('name', flat=True):
        name = name.replace(title, '')
        name = name.replace(unidecode(title), '')
    return whitespaces_clean(name)


def remove_club_sponsor(name: str) -> str:
    if '-' in name:
        parts = name.split('-')
        maybe_club, maybe_sponsor = parts[0].strip(), parts[1].strip()

        # check if the first part is a club
        query = Entity.queryset_for_search().filter(
            Q(name__unaccent__icontains=maybe_club) | Q(joined_names__unaccent__icontains=maybe_club), type=ENTITY_CLUB
        )
        if not maybe_club or not query.exists():
            maybe_club = None

        # check if the second part is a club
        query = Entity.queryset_for_search().filter(
            Q(name__unaccent__icontains=maybe_sponsor) | Q(joined_names__unaccent__icontains=maybe_sponsor), type=ENTITY_CLUB
        )
        if not maybe_sponsor or not query.exists():
            maybe_sponsor = None

        if all(i is None for i in [maybe_club, maybe_sponsor]):
            return name

        name = ' - '.join(i for i in [maybe_club, maybe_sponsor] if i is not None)
    return whitespaces_clean(name)
