import { http } from './http'
import type {
  DatapointCreate,
  DatapointListItem,
  DatapointOut,
  DatapointRawOut,
  ExportRequest,
  SessionCreate,
  SessionOut,
  TagCreate,
  TagOut,
  UUID,
  UserOut,
  UserSummary,
} from './types'

export const kruzinatorApi = {
  async health(): Promise<Record<string, unknown>> {
    const { data } = await http.get('/health')
    return data
  },

  async createUser(): Promise<UserOut> {
    const { data } = await http.post('/api/v1/users', {})
    return data
  },

  async getUser(userId: UUID): Promise<UserSummary> {
    const { data } = await http.get(`/api/v1/users/${userId}`)
    return data
  },

  async deleteUser(userId: UUID): Promise<void> {
    await http.delete(`/api/v1/users/${userId}`)
  },

  async createSession(payload: SessionCreate): Promise<SessionOut> {
    const { data } = await http.post('/api/v1/sessions', payload)
    return data
  },

  async createDatapoint(payload: DatapointCreate): Promise<DatapointOut> {
    const { data } = await http.post('/api/v1/datapoints', payload)
    return data
  },

  async listUserDatapoints(userId: UUID): Promise<DatapointListItem[]> {
    const { data } = await http.get(`/api/v1/users/${userId}/datapoints`)
    return data
  },

  async getDatapoint(datapointId: UUID): Promise<DatapointOut> {
    const { data } = await http.get(`/api/v1/datapoints/${datapointId}`)
    return data
  },

  async getDatapointRaw(datapointId: UUID): Promise<DatapointRawOut> {
    const { data } = await http.get(`/api/v1/datapoints/${datapointId}/raw`)
    return data
  },

  async addTag(datapointId: UUID, payload: TagCreate): Promise<TagOut> {
    const { data } = await http.post(`/api/v1/datapoints/${datapointId}/tags`, payload)
    return data
  },

  async exportDataset(payload: ExportRequest): Promise<unknown> {
    const { data } = await http.post('/api/v1/exports', payload)
    return data
  },
}
