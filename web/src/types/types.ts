export type RaceType = 'TIME_TRIAL' | 'CONVENTIONAL';
export type Gender = 'MALE' | 'FEMALE' | 'MIX';
export type PenaltyReason = 'NO_LINE_START' | 'NULL_START' | 'BLADE_TOUCH'
export type ParticipantCategory = 'ABSOLUT' | 'VETERAN' | 'SCHOOL'

export class StringTypeUtils {
  static raceType(type?: RaceType) {
    switch (type) {
      case "TIME_TRIAL":
        return "CONTRARRELOJ"
      case "CONVENTIONAL":
        return "CONVENCIONAL"
      default:
        return ""
    }
  }

  static reason(reason?: PenaltyReason) {
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

  static gender(gender?: Gender) {
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

  static category(category?: ParticipantCategory) {
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

  static categoryGender([category, gender]: [ParticipantCategory, Gender | null]) {
    return gender
      ? `${StringTypeUtils.category(category)} ${StringTypeUtils.gender(gender)}`
      : `${StringTypeUtils.category(category)}`
  }
}
