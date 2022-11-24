export type RequestModel = 'RACE' | 'PARTICIPANT' | 'ENTITY'
export type RequestType = 'CREATE' | 'UPDATE'

export interface RequestChange {
  key: string;
  value: string;
}

export interface Request {
  model: RequestModel;
  type: RequestType;
  target_id?: number;
  changes: RequestChange[]
}
