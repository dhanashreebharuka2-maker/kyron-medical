"use client";

import { OfficeInfoCard } from "./OfficeInfoCard";
import { AppointmentSummaryCard } from "./AppointmentSummaryCard";
import { PhoneCallCard } from "./PhoneCallCard";
import type { SessionState } from "@/types/session";

type Office = {
  name: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  zip: string;
  phone: string;
  hours: Record<string, string>;
  parking?: string;
};

type Props = {
  office?: Office;
  session: SessionState | null;
  sessionId: string | null;
  onSessionUpdate: (s: SessionState) => void;
};

export function OfficeInfoSidebar({ office, session, sessionId, onSessionUpdate }: Props) {
  return (
    <aside className="flex flex-col gap-4 lg:sticky lg:top-8 lg:max-h-[min(88vh,920px)] lg:overflow-y-auto">
      <PhoneCallCard sessionId={sessionId} onSessionUpdate={onSessionUpdate} />
      {session && <AppointmentSummaryCard session={session} />}
      {office && <OfficeInfoCard office={office} />}
    </aside>
  );
}
