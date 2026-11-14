import type { Role } from "@/lib/types";

// Display layer over the backend's role names (back/app/core/roles.py).
export const roleLabel: Record<string, string> = {
  admin: "Admin",
  staff: "Staff",
  member: "Membre",
};

/** Plural, lower-case — for sentences like "Notifier les membres". */
export const roleLabelPlural: Record<string, string> = {
  admin: "admins",
  staff: "membres du staff",
  member: "membres",
};

export const roleToneClass: Record<string, string> = {
  admin: "text-role-admin decoration-role-admin",
  staff: "text-role-tresorier decoration-role-tresorier",
  member: "text-role-user decoration-role-user",
};

export function labelOf(role: Role | string) {
  const name = typeof role === "string" ? role : role.name;
  return roleLabel[name] ?? name;
}

export function initialsOf(...parts: (string | null | undefined)[]) {
  return parts
    .filter(Boolean)
    .map((p) => p![0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function fullName(user: { firstname: string; name: string }) {
  return `${user.firstname} ${user.name}`;
}
