export type UUID = string

export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue }
export type JsonObject = { [key: string]: JsonValue }

export interface UserOut {
  id: UUID
  created_at: string
}

export interface UserSummary {
  id: UUID
  created_at: string
  datapoints_count: number
  sessions_count: number
}

export interface Point {
  x: number
  y: number
  tMs: number
  pressure?: number | null
  tiltX?: number | null
  tiltY?: number | null
  azimuth?: number | null
}

export interface DatapointCreate {
  user_id: UUID
  session_id?: UUID | null
  capture_label?: string
  protocol_version?: string
  metadata: JsonObject
  points: Point[]
}

export interface DatapointListItem {
  id: UUID
  created_at: string
  capture_label: string
  protocol_version: string
  metadata: JsonObject
  features: JsonObject
}

export interface DatapointOut {
  id: UUID
  user_id: UUID
  session_id: UUID | null
  created_at: string
  capture_label: string
  protocol_version: string
  metadata: JsonObject
  features: JsonObject
}

export interface DatapointRawOut {
  id: UUID
  raw: JsonObject
}

export interface TagCreate {
  tag?: string | null
  note?: string | null
}

export interface TagOut {
  id: UUID
  datapoint_id: UUID
  created_at: string
  tag: string | null
  note: string | null
}

export interface SessionCreate {
  user_id?: UUID | null
  protocol_version?: string
  prompt_plan: JsonObject
}

export interface SessionOut {
  id: UUID
  user_id: UUID | null
  protocol_version: string
  prompt_plan: JsonObject
  started_at: string
}

export interface ExportRequest {
  user_ids?: UUID[] | null
  protocol_version?: string | null
  created_from?: string | null
  created_to?: string | null
}
