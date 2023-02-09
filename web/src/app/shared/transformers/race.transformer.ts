import { Race, RaceDetail } from "src/types";
import { int2roman } from "../strings";
import * as dayjs from "dayjs";
import "dayjs/locale/es";

export class RaceTransformer {
  static transformRace(race: Race): Race {
    dayjs.locale("es");

    race.date = dayjs(race.date).format('DD/MM/YYYY')
    race.is_female = race.gender == 'FEMALE';
    race.name = this.formatRace(race)
    return race;
  }

  static transformRaceDetails(race: RaceDetail): RaceDetail {
    this.transformRace(race)
    return race;
  }

  private static formatRace(race: Race): string {
    const day = (race.day > 1) ? `XORNADA ${race.day}` : '';
    const gender = race.is_female ? `(FEMENINA)` : '';

    const trophy = race.trophy && race.trophy_edition
      ? `${int2roman(race.trophy_edition)} - ${race.trophy.name}`.replace('(CLASIFICATORIA)', '')
      : '';
    const flag = race.flag && race.flag_edition ? `${int2roman(race.flag_edition)} - ${race.flag.name}` : '';
    const name = [trophy, flag, race.sponsor].filter(x => !!x).join(' - ');
    return `${name} ${day} ${gender}`.replace(/\s+/g, ' ').trim();
  }
}
