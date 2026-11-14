// Mirrors of back/app/schemas/classes.py — the backend is the source of truth.
// Datetimes arrive as ISO strings without a timezone. User-entered ones (events,
// reminders) are local: `new Date()`. Server-generated ones (notification `date`,
// `linked_at`) are UTC: `parseServerDate()` from lib/format.

export type { Page, Role, UserOut } from "@/lib/auth/types";

export type NotificationOut = {
  id: number;
  date: string;
  message: string;
  from_id: number | null;
  read: boolean;
};

export type ReminderOut = {
  id: number;
  date: string;
  title: string;
  description: string | null;
};

export type EventOut = {
  id: number;
  title: string;
  description: string | null;
  start_date: string;
  end_date: string;
  registrations_limits: number;
  creator_id: number | null;
  registered_count: number;
  spots_left: number;
  is_full: boolean;
  registered_user_ids: number[];
  staff_ids: number[];
  attendee_ids: number[];
};

/** `FileNode` from the storage routes (Nextcloud, acting as the current user). */
export type StorageNode = {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  mime_type: string;
  last_modified: string;
  etag: string;
  file_id: string;
};

/** Shape returned by the admin-only `GET /nextcloud/files/{username}`. */
export type AdminFileEntry = {
  name: string;
  is_dir: boolean;
  size: number;
};

/** `POST /nextcloud/link/init` — open `login_url`, then poll with `handle`. */
export type NcLinkInit = {
  login_url: string;
  handle: string;
  expires_in: number;
};

export type NcLinkPoll = {
  status: "pending" | "linked";
  nc_username: string | null;
};

export type NcLinkStatus = {
  linked: boolean;
  nc_username: string | null;
  linked_at: string | null;
};

// --- Not backed by the API yet (mock data only) ---

export type BudgetRequest = {
  id: string;
  date: Date;
  name: string;
  reason: string;
  amountEur: number;
};

/** Display names by user id, for lists of participants. Only admins can build it. */
export type PeopleById = Record<number, { firstname: string; name: string; username: string }>;
