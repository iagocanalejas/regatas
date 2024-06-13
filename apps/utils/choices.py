from rscraping.data.constants import (
    BOAT_WEIGHT_LIMIT,
    CATEGORY_ABSOLUT,
    CATEGORY_ALL,
    CATEGORY_SCHOOL,
    CATEGORY_VETERAN,
    COLLISION,
    COVID_ABSENCE,
    COXWAIN_WEIGHT_LIMIT,
    ENTITY_CLUB,
    ENTITY_FEDERATION,
    ENTITY_LEAGUE,
    ENTITY_PRIVATE,
    GENDER_ALL,
    GENDER_FEMALE,
    GENDER_MALE,
    GENDER_MIX,
    NO_LINE_START,
    NULL_START,
    OFF_THE_FIELD,
    RACE_BATEL,
    RACE_CONVENTIONAL,
    RACE_TIME_TRIAL,
    RACE_TRAINERA,
    RACE_TRAINERILLA,
    SINKING,
    STARBOARD_TACK,
    WRONG_LINEUP,
    WRONG_ROUTE,
)

################
#   RACE TYPE  #
################
RACE_TYPES = [RACE_CONVENTIONAL, RACE_TIME_TRIAL]
RACE_TYPE_CHOICES = [
    (RACE_CONVENTIONAL, "Convencional"),
    (RACE_TIME_TRIAL, "Contrarreloj"),
]

################
#  MODALITIES  #
################
RACE_MODALITIES = [RACE_TRAINERA, RACE_TRAINERILLA, RACE_BATEL]
RACE_MODALITY_CHOICES = [
    (RACE_TRAINERA, "Trainera"),
    (RACE_TRAINERILLA, "Trainerilla"),
    (RACE_BATEL, "Batel"),
]

################
#  CATEGORIES  #
################
PARTICIPANT_CATEGORIES = [CATEGORY_ABSOLUT, CATEGORY_VETERAN, CATEGORY_SCHOOL]
PARTICIPANT_CATEGORIES_CHOICES = [
    (CATEGORY_ABSOLUT, "Absoluto"),
    (CATEGORY_VETERAN, "Veterano"),
    (CATEGORY_SCHOOL, "Escuela"),
]

################
#   ENTITIES   #
################
ENTITY_TYPES = [ENTITY_CLUB, ENTITY_LEAGUE, ENTITY_FEDERATION, ENTITY_PRIVATE]
ENTITY_TYPE_CHOICES = [
    (ENTITY_CLUB, "Club"),
    (ENTITY_LEAGUE, "Liga"),
    (ENTITY_FEDERATION, "Federación"),
    (ENTITY_PRIVATE, "Privada"),
]

################
#   GENDERS    #
################
GENDERS = [GENDER_MALE, GENDER_FEMALE, GENDER_MIX]
GENDER_CHOICES = [
    (GENDER_MALE, "Male"),
    (GENDER_FEMALE, "Female"),
    (GENDER_MIX, "Mixto"),
]
CATEGORY_CHOICES = [
    (CATEGORY_SCHOOL, "School"),
    (CATEGORY_ABSOLUT, "Absolut"),
    (CATEGORY_VETERAN, "Veteran"),
]
RACE_GENDER_CHOICES = [
    (GENDER_MALE, "Male"),
    (GENDER_FEMALE, "Female"),
    (GENDER_ALL, "All"),
]
RACE_CATEGORY_CHOICES = [
    (CATEGORY_ALL, "All"),
    (CATEGORY_SCHOOL, "School"),
    (CATEGORY_ABSOLUT, "Absolut"),
    (CATEGORY_VETERAN, "Veteran"),
]
################
#  PENALTIES   #
################
PENALTY_CHOICES = [
    (BOAT_WEIGHT_LIMIT, "Fuera de peso"),
    (COLLISION, "Colisión"),
    (COVID_ABSENCE, "Ausencia por COVID-19"),
    (COXWAIN_WEIGHT_LIMIT, "Timonel fuera de peso"),
    (NO_LINE_START, "Salida sin estacha"),
    (NULL_START, "Salida nula"),
    (OFF_THE_FIELD, "Fuera de campo"),
    (SINKING, "Hundimiento"),
    (STARBOARD_TACK, "Virada por estribor"),
    (WRONG_LINEUP, "Alineación incorrecta"),
    (WRONG_ROUTE, "Ruta/Llegada incorrecta"),
]
