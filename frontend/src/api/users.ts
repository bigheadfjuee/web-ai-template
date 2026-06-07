export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface User {
  id: string
  username: string
  email: string
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
}

export interface UserUpdate {
  username?: string
  email?: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let message = res.statusText
    try {
      const body = (await res.json()) as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // ignore parse errors — keep statusText
    }
    throw new ApiError(res.status, message)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function listUsers(skip = 0, limit = 100): Promise<User[]> {
  return request<User[]>(`/api/users?skip=${skip}&limit=${limit}`)
}

export function getUser(id: string): Promise<User> {
  return request<User>(`/api/users/${id}`)
}

export function createUser(data: UserCreate): Promise<User> {
  return request<User>('/api/users', { method: 'POST', body: JSON.stringify(data) })
}

export function updateUser(id: string, data: UserUpdate): Promise<User> {
  return request<User>(`/api/users/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deleteUser(id: string): Promise<void> {
  return request<void>(`/api/users/${id}`, { method: 'DELETE' })
}
