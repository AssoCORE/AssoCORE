"use client";

import { Megaphone } from "lucide-react";
import { useState, useTransition } from "react";

import { SearchBar } from "@/components/custom/search-bar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useUrlParam, useUrlSearch } from "@/hooks/use-url-search";
import { broadcastNotification } from "@/lib/actions";
import { ROLE_ADMIN, ROLE_MEMBER, ROLE_STAFF } from "@/lib/auth/roles";
import { roleLabel, roleLabelPlural } from "@/lib/roles";
import { notificationMessageError } from "@/lib/schemas";

const roles = [ROLE_MEMBER, ROLE_STAFF, ROLE_ADMIN];

export function UsersSearch() {
  const search = useUrlSearch();
  // GET /user/?role= filters in SQL; "" means every role.
  const role = useUrlParam("role");
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  function onBroadcast() {
    const target = role.value ? `les ${roleLabelPlural[role.value] ?? role.value}` : "tous les adhérents";
    const text = window.prompt(`Message à envoyer à ${target}`)?.trim();
    if (!text) return;
    const invalid = notificationMessageError(text);
    if (invalid) {
      setMessage({ ok: false, text: invalid });
      return;
    }
    setMessage(null);
    startTransition(async () => {
      const res = await broadcastNotification(text, role.value || null);
      setMessage(
        res.ok
          ? { ok: true, text: `Notification envoyée à ${res.data} adhérent(s).` }
          : { ok: false, text: res.error },
      );
    });
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <SearchBar
          className="flex-1"
          value={search.value}
          onChange={search.setValue}
          placeholder="Rechercher par nom, utilisateur ou email"
          filterActive={!!role.value}
          filters={
            <>
              <DropdownMenuLabel>Rôle</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup value={role.value} onValueChange={role.setValue}>
                <DropdownMenuRadioItem value="">Tous les rôles</DropdownMenuRadioItem>
                {roles.map((r) => (
                  <DropdownMenuRadioItem key={r} value={r}>
                    {roleLabel[r]}
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
            </>
          }
        />
        <Button variant="outline" onClick={onBroadcast} disabled={pending}>
          <Megaphone />
          Notifier {role.value ? `les ${roleLabelPlural[role.value] ?? role.value}` : "tous"}
        </Button>
      </div>
      {message && (
        <p className={message.ok ? "text-sm text-primary" : "text-sm text-destructive"}>
          {message.text}
        </p>
      )}
    </div>
  );
}
