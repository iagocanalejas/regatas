export type RaceType = 'TIME_TRIAL' | 'CONVENTIONAL';
export type Gender = 'MALE' | 'FEMALE' | 'MIX';
export type PenaltyReason = 'NO_LINE_START' | 'NULL_START' | 'BLADE_TOUCH'
export type ParticipantCategory = 'ABSOLUT' | 'VETERAN' | 'SCHOOL'

export function readableReason(reason?: PenaltyReason): string {
  switch (reason) {
    case "BLADE_TOUCH":
      return 'TOQUE DE PALAS'
    case "NO_LINE_START":
      return 'SALIDA SIN ESTACHA'
    case "NULL_START":
      return 'SALIDA NULA'
    default:
      return 'DESCONOCIDO'
  }
}

export function readableGender(gender?: Gender): string {
  switch (gender) {
    case "MALE":
      return 'MASCULINO'
    case "FEMALE":
      return 'FEMENINO'
    case "MIX":
      return 'MIXTO'
    default:
      return 'DESCONOCIDO'
  }
}

export function readableCategory(category?: ParticipantCategory): string {
  switch (category) {
    case "ABSOLUT":
      return 'ABSOLUTO'
    case "VETERAN":
      return 'VETERANO'
    case "SCHOOL":
      return 'ESCUELA'
    default:
      return 'DESCONOCIDO'
  }
}
