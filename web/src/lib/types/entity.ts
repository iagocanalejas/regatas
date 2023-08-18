import type { League } from './league';
// import type { Participation } from './participant';
// import type { Page } from './page';

export type Entity = {
	id: number;
	name: string;
};
export type Club = Entity;

export type ClubDetail = Club & {
	// participation: Page<Participation>;
};
export type Organizers = {
	clubs: Club[];
	leagues: League[];
	federations: Entity[];
	private: Entity[];
};
