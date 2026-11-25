"use client";

import { MoreHorizontal, UserCheck, UserX } from "lucide-react";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { setNextcloudUserEnabled } from "@/lib/actions";

// GET /nextcloud/users returns bare usernames, without the enabled state, so both
// actions are always offered and the result is reported back.
export function NcAccountMenu({ username }: { username: string }) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(
    null
  );

  function set(enabled: boolean) {
    setMessage(null);
    startTransition(async () => {
      const res = await setNextcloudUserEnabled(username, enabled);
      setMessage(
        res.ok
          ? { ok: true, text: enabled ? "Compte activé." : "Compte désactivé." }
          : { ok: false, text: res.error }
      );
    });
  }

  return (
    <div className="flex shrink-0 items-center gap-2">
      {message && (
        <span
          className={
            message.ok ? "text-xs text-primary" : "text-xs text-destructive"
          }
        >
          {message.text}
        </span>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Compte Nextcloud"
            disabled={pending}
          >
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={() => set(true)}>
            <UserCheck className="mr-2 size-4" />
            Activer le compte Nextcloud
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-brand-red focus:text-brand-red"
            onSelect={() => {
              if (
                window.confirm(
                  `Désactiver le compte Nextcloud « ${username} » ?`
                )
              )
                set(false);
            }}
          >
            <UserX className="mr-2 size-4" />
            Désactiver le compte Nextcloud
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
