export const RACE_TYPES = ['TIME_TRIAL', 'CONVENTIONAL'] as const;
export type RaceType = (typeof RACE_TYPES)[number];
export const raceType_es: { [_ in RaceType]: string } = {
	TIME_TRIAL: 'CONTRARRELOJ',
	CONVENTIONAL: 'CONVENCIONAL'
};

export const PENALTY_REASONS = ['NO_LINE_START', 'NULL_START', 'BLADE_TOUCH'] as const;
export type PenaltyReason = (typeof PENALTY_REASONS)[number];
export const penaltyReason_es: { [_ in PenaltyReason]: string } = {
	NO_LINE_START: 'TOQUE DE PALAS',
	NULL_START: 'SALIDA SIN ESTACHA',
	BLADE_TOUCH: 'SALIDA NULA'
};

export const GENDERS = ['MALE', 'FEMALE', 'MIX'] as const;
export type Gender = (typeof GENDERS)[number];
export const gender_es: { [_ in Gender]: string } = {
	MALE: 'MASCULINO',
	FEMALE: 'FEMENINO',
	MIX: 'MIXTO'
};

export const PARTICIPANT_CATEGORIES = ['ABSOLUT', 'VETERAN', 'SCHOOL'] as const;
export type ParticipantCategory = (typeof PARTICIPANT_CATEGORIES)[number];
export const category_es: { [_ in ParticipantCategory]: string } = {
	ABSOLUT: 'ABSOLUTO',
	VETERAN: 'VETERANO',
	SCHOOL: 'ESCUELA'
};

export function categoryGender_es([category, gender]: [ParticipantCategory, Gender | null]) {
	return gender ? `${category_es[category]} ${gender_es[gender]}` : `${category_es[category]}`;
}
