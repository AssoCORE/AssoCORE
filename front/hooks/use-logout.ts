"use client";

import { useRouter } from "next/navigation";

/**
 * `everywhere` revokes every session of the user (all devices). It resolves to an
 * error message when that failed — the current session is then kept.
 */
export function useLogout() {
  const router = useRouter();
  return async (everywhere = false): Promise<string | null> => {
    const res = await fetch(`/api/auth/logout${everywhere ? "?all=1" : ""}`, {
      method: "POST",
    }).catch(() => null);
    if (everywhere && !res?.ok) {
      const body = await res?.json().catch(() => null);
      return typeof body?.detail === "string"
        ? body.detail
        : "Service indisponible.";
    }
    router.push("/login");
    router.refresh();
    return null;
  };
}
