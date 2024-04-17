from rscraping.data.constants import (
    BLADE_TOUCH,
    CATEGORY_ABSOLUT,
    CATEGORY_SCHOOL,
    CATEGORY_VETERAN,
    COLISION,
    COVID_ABSENCE,
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
RACE_GENDER_CHOICES = [
    (GENDER_MALE, "Male"),
    (GENDER_FEMALE, "Female"),
    (GENDER_ALL, "All"),
]
################
#  PENALTIES   #
################
PENALTY_CHOICES = [
    (NO_LINE_START, "Salida sin estacha"),
    (NULL_START, "Salida nula"),
    (COLISION, "Colisión"),
    (BLADE_TOUCH, "Toque de palas"),
    (OFF_THE_FIELD, "Fuera de campo"),
    (COVID_ABSENCE, "Ausencia por COVID-19"),
]
