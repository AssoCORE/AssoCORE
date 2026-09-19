export interface Role {
  id: number;
  name: string;
}

export interface UserOut {
  id: number;
  name: string;
  firstname: string;
  username: string;
  mail: string;
  phone: string | null;
  birth_date: string | null;
  roles: Role[];
  notifications: unknown[];
  reminders: unknown[];
}

/** Mirrors the backend's `Page[T]` envelope (`back/app/schemas/classes.py`). */
export interface Page<T> {
  items: T[];
  /** Rows matching the filters before limit/offset — use it for page counts. */
  total: number;
  limit: number;
  offset: number;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}
