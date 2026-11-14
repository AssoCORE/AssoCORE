import { Bell, Calendar } from "lucide-react";
import Link from "next/link";

import { EventListItem } from "@/components/custom/event-list-item";
import { NotificationItem } from "@/components/custom/notification-item";
import { PageHeader } from "@/components/custom/page-header";
import { SectionCard } from "@/components/custom/section-card";
import { Button } from "@/components/ui/button";
import { apiJson } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth/session";
import { fullName } from "@/lib/roles";
import type { EventOut, NotificationOut, Page } from "@/lib/types";

export default async function Home() {
  const [user, events, notifications] = await Promise.all([
    getCurrentUser(),
    apiJson<Page<EventOut>>("/event/?upcoming=true&limit=3").catch(() => null),
    apiJson<Page<NotificationOut>>("/user/notification/?limit=5").catch(() => null),
  ]);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <PageHeader title={`Bienvenue, ${user ? fullName(user) : ""}`} />

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 md:grid-cols-2">
        <SectionCard
          className="h-full"
          title="Événements à venir"
          icon={<Calendar className="size-4 text-primary" />}
          footer={
            <Button
              asChild
              variant="outline"
              className="w-full border-primary/30 text-sm hover:bg-primary/5"
            >
              <Link href="/event">Voir plus d&apos;évènements</Link>
            </Button>
          }
        >
          {!events ? (
            <Empty>Impossible de charger les événements.</Empty>
          ) : events.items.length === 0 ? (
            <Empty>Aucun événement à venir.</Empty>
          ) : (
            events.items.map((event) => <EventListItem key={event.id} event={event} />)
          )}
        </SectionCard>

        <SectionCard
          className="h-full"
          title="Notifications récentes"
          icon={<Bell className="size-4 text-primary" />}
        >
          {!notifications ? (
            <Empty>Impossible de charger les notifications.</Empty>
          ) : notifications.items.length === 0 ? (
            <Empty>Aucune notification.</Empty>
          ) : (
            notifications.items.map((n) => <NotificationItem key={n.id} notification={n} />)
          )}
        </SectionCard>
      </div>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}
