import { Calendar, User } from "lucide-react";
import Link from "next/link";

import { ActivityItem } from "@/components/custom/activity-item";
import { EventListItem } from "@/components/custom/event-list-item";
import { PageHeader } from "@/components/custom/page-header";
import { SectionCard } from "@/components/custom/section-card";
import { Button } from "@/components/ui/button";
import { events, recentActivity } from "@/lib/mock/events";
import { currentProfile } from "@/lib/mock/users";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <PageHeader title={`Bienvenue, ${currentProfile.fullName}`} />

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
          {events.slice(0, 3).map((event) => (
            <EventListItem key={event.id} event={event} />
          ))}
        </SectionCard>

        <SectionCard
          className="h-full"
          title="Activité Récente"
          icon={<User className="size-4 text-primary" />}
        >
          {recentActivity.map((activity) => (
            <ActivityItem key={activity.id} activity={activity} />
          ))}
        </SectionCard>
      </div>
    </div>
  );
}
