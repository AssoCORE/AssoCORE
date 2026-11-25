"use client";

import { useState, useTransition } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import {
  deleteEvent,
  registerForEvent,
  unregisterFromEvent,
} from "@/lib/actions";
import { hasRole, isAdmin, ROLE_ADMIN, ROLE_STAFF } from "@/lib/auth/roles";
import type { EventOut } from "@/lib/types";

/**
 * What the current user may do with an event, and the actions themselves.
 * Permissions are UX only — the backend re-checks each of these on every call.
 */
export function useEventActions(
  event: EventOut,
  { onDeleted }: { onDeleted?: () => void } = {}
) {
  const user = useAuth();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const privileged = hasRole(user, ROLE_ADMIN, ROLE_STAFF);
  const registered = event.registered_user_ids.includes(user.id);

  function toggleRegistration() {
    setError(null);
    startTransition(async () => {
      const res = registered
        ? await unregisterFromEvent(event.id)
        : await registerForEvent(event.id);
      if (!res.ok) setError(res.error);
    });
  }

  function remove() {
    if (
      !window.confirm(
        `Supprimer « ${event.title} » ? Les inscrits seront notifiés.`
      )
    )
      return;
    setError(null);
    startTransition(async () => {
      const res = await deleteEvent(event.id);
      if (!res.ok) setError(res.error);
      else onDeleted?.();
    });
  }

  return {
    pending,
    error,
    registered,
    past: new Date(event.end_date) < new Date(),
    privileged,
    canEdit: privileged || event.creator_id === user.id,
    canDelete: isAdmin(user),
    toggleRegistration,
    remove,
  };
}

/** Badge shown on an event: the user's registration, or how many places remain. */
export function eventStatus(event: EventOut, registered: boolean) {
  if (registered) {
    return {
      label: "Inscrit",
      className: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
    };
  }
  if (event.is_full) {
    return {
      label: "Complet",
      className: "bg-red-100 text-red-800 hover:bg-red-100",
    };
  }
  return {
    label: `${event.spots_left} place${event.spots_left > 1 ? "s" : ""}`,
    className: "bg-sky-100 text-sky-800 hover:bg-sky-100",
  };
}
