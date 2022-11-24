import { Race, RaceDetail } from "src/types";
import * as moment from "moment/moment";
import { int2roman } from "../strings";

export class RaceTransformer {
  static transformRace(race: Race): Race {
    moment.locale("es");

    race.date = moment(race.date).format('L')
    race.is_female = (race.league && race.league.gender == 'FEMALE') || race.gender == 'FEMALE';
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
    const modality = race.modality === 'VETERAN' ? `(VETERANOS)` : '';

    const trophy = race.trophy && race.trophy_edition
      ? `${int2roman(race.trophy_edition)} - ${race.trophy.name}`.replace('(CLASIFICATORIA)', '')
      : '';
    const flag = race.flag && race.flag_edition ? `${int2roman(race.flag_edition)} - ${race.flag.name}` : '';
    const name = [trophy, flag, race.sponsor].filter(x => !!x).join(' - ');
    return `${name} ${day} ${gender} ${modality}`.replace(/\s+/g, ' ').trim();
  }
}
