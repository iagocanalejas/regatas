from rscraping.data.constants import *

################
#   RACE TYPE  #
################
RACE_TYPES = [RACE_CONVENTIONAL, RACE_TIME_TRIAL]
RACE_TYPE_CHOICES = [
    (RACE_CONVENTIONAL, 'Convencional'),
    (RACE_TIME_TRIAL, 'Contrarreloj'),
]

################
#  MODALITIES  #
################
RACE_MODALITIES = [RACE_TRAINERA, RACE_TRAINERILLA, RACE_BATEL]
RACE_MODALITY_CHOICES = [
    (RACE_TRAINERA, 'Trainera'),
    (RACE_TRAINERILLA, 'Trainerilla'),
    (RACE_BATEL, 'Batel'),
]

################
#  CATEGORIES  #
################
PARTICIPANT_CATEGORIES = [PARTICIPANT_CATEGORY_ABSOLUT, PARTICIPANT_CATEGORY_VETERAN, PARTICIPANT_CATEGORY_SCHOOL]
PARTICIPANT_CATEGORIES_CHOICES = [
    (PARTICIPANT_CATEGORY_ABSOLUT, 'Absoluto'),
    (PARTICIPANT_CATEGORY_VETERAN, 'Veterano'),
    (PARTICIPANT_CATEGORY_SCHOOL, 'Escuela'),
]

################
#   ENTITIES   #
################
ENTITY_TYPES = [ENTITY_CLUB, ENTITY_LEAGUE, ENTITY_FEDERATION, ENTITY_PRIVATE]
ENTITY_TYPE_CHOICES = [
    (ENTITY_CLUB, 'Club'),
    (ENTITY_LEAGUE, 'Liga'),
    (ENTITY_FEDERATION, 'Federación'),
    (ENTITY_PRIVATE, 'Privada'),
]

################
#   GENDERS    #
################
GENDERS = [GENDER_MALE, GENDER_FEMALE, GENDER_MIX]
GENDER_CHOICES = [
    (GENDER_MALE, 'Male'),
    (GENDER_FEMALE, 'Female'),
    (GENDER_MIX, 'Mixto'),
]

################
#  PENALTIES   #
################
PENALTY_CHOICES = [
    (NO_LINE_START, 'Salida sin estacha'),
    (NULL_START, 'Salida nula'),
    (BLADE_TOUCH, 'Toque de palas'),
]
