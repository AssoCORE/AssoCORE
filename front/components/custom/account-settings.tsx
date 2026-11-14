"use client";

import { Cloud, LogOut, Trash2, Unlink } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/use-logout";
import { deleteMe, pollNextcloudLink, startNextcloudLink, unlinkNextcloud } from "@/lib/actions";
import { parseServerDate } from "@/lib/format";
import type { NcLinkStatus } from "@/lib/types";

const POLL_MS = 2000;

export function AccountSettings({ link }: { link: NcLinkStatus | null }) {
  const router = useRouter();
  const logout = useLogout();
  const [pending, startTransition] = useTransition();
  const [linking, setLinking] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (pollTimer.current) clearTimeout(pollTimer.current);
  }, []);

  // Login Flow v2: open Nextcloud's approval page, then poll until the user
  // approves there. The tab is opened synchronously so popup blockers allow it.
  async function onLink() {
    const tab = window.open("about:blank", "_blank");
    setMessage(null);
    setLinking(true);
    const init = await startNextcloudLink();
    if (!init.ok) {
      tab?.close();
      setLinking(false);
      setMessage({ ok: false, text: init.error });
      return;
    }
    if (tab) {
      tab.opener = null;
      tab.location.href = init.data.login_url;
    }
    else window.location.assign(init.data.login_url);

    const deadline = Date.now() + init.data.expires_in * 1000;
    const poll = async () => {
      const res = await pollNextcloudLink(init.data.handle);
      if (res.ok && res.data.status === "linked") {
        setLinking(false);
        setMessage({ ok: true, text: `Compte Nextcloud « ${res.data.nc_username} » lié.` });
        router.refresh();
      } else if (!res.ok) {
        setLinking(false);
        setMessage({ ok: false, text: res.error });
      } else if (Date.now() > deadline) {
        setLinking(false);
        setMessage({ ok: false, text: "La demande de liaison a expiré, recommencez." });
      } else {
        pollTimer.current = setTimeout(poll, POLL_MS);
      }
    };
    pollTimer.current = setTimeout(poll, POLL_MS);
  }

  function onUnlink() {
    if (
      !window.confirm(
        "Délier votre compte Nextcloud ? Pensez à révoquer le mot de passe d'application dans Nextcloud (Paramètres → Sécurité).",
      )
    ) {
      return;
    }
    setMessage(null);
    startTransition(async () => {
      const res = await unlinkNextcloud();
      setMessage(res.ok ? { ok: true, text: "Compte Nextcloud délié." } : { ok: false, text: res.error });
    });
  }

  function onLogoutEverywhere() {
    if (!window.confirm("Fermer la session sur tous vos appareils ?")) return;
    setMessage(null);
    startTransition(async () => {
      const error = await logout(true);
      if (error) setMessage({ ok: false, text: error });
    });
  }

  function onDeleteAccount() {
    if (
      !window.confirm(
        "Supprimer définitivement votre compte et votre espace Nextcloud ? Cette action est irréversible.",
      )
    ) {
      return;
    }
    setMessage(null);
    startTransition(async () => {
      const res = await deleteMe();
      if (res.ok) {
        router.push("/login");
        router.refresh();
      } else {
        setMessage({ ok: false, text: res.error });
      }
    });
  }

  const busy = pending || linking;

  return (
    <section className="flex flex-col gap-3 border-t border-border pt-4">
      <h2 className="text-sm font-semibold">Compte</h2>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          {link === null
            ? "Statut Nextcloud indisponible."
            : link.linked
              ? `Nextcloud lié à « ${link.nc_username} »${
                  link.linked_at
                    ? ` depuis le ${format(parseServerDate(link.linked_at), "d MMMM yyyy", { locale: fr })}`
                    : ""
                }.`
              : "Votre compte Nextcloud n'est pas lié."}
        </p>
        {link?.linked ? (
          <Button variant="outline" size="sm" onClick={onUnlink} disabled={busy}>
            <Unlink />
            Délier Nextcloud
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={onLink} disabled={busy || link === null}>
            <Cloud />
            {linking ? "En attente de validation…" : "Lier mon compte Nextcloud"}
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <Button variant="outline" size="sm" onClick={onLogoutEverywhere} disabled={busy}>
          <LogOut />
          Déconnecter tous les appareils
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-brand-red hover:text-brand-red"
          onClick={onDeleteAccount}
          disabled={busy}
        >
          <Trash2 />
          Supprimer mon compte
        </Button>
      </div>

      {message && (
        <p className={message.ok ? "text-sm text-primary" : "text-sm text-destructive"}>
          {message.text}
        </p>
      )}
    </section>
  );
}
