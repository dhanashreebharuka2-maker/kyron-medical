export type Patient = {
  first_name: string | null;
  last_name: string | null;
  dob: string | null;
  phone: string | null;
  email: string | null;
};

export type Provider = {
  id: string;
  full_name: string;
  specialty: string;
  body_part_focus: string;
  description: string;
};

export type Slot = {
  id: string;
  provider_id: string;
  start_iso: string;
  end_iso: string;
  duration_minutes: number;
};

export type Booking = {
  slot_id: string;
  provider_id: string;
  provider_name: string;
  specialty: string;
  start_iso: string;
  end_iso: string;
  office_name: string;
  office_address: string;
  office_phone: string;
  confirmed_at: string;
};

export type SessionState = {
  session_id: string;
  workflow: string | null;
  patient: Patient;
  reason_for_visit: string | null;
  matched_provider_id: string | null;
  matched_provider: Provider | null;
  intake_complete: boolean;
  slot_query: string | null;
  shown_slots: Slot[];
  selected_slot_id: string | null;
  booking: Booking | null;
  booking_confirmed: boolean;
  email_sent: boolean;
  /** True when no real email API sent (demo / missing RESEND_API_KEY). */
  email_mock?: boolean;
  sms_opt_in: boolean | null;
  sms_sent: boolean;
  /** True when no real Twilio send (demo / missing credentials). */
  sms_mock?: boolean;
  /** Twilio/API error text when a send was attempted and failed. */
  sms_last_error?: string | null;
  /** Twilio Message SID when the API accepted the SMS (lookup in Twilio Logs). */
  sms_message_sid?: string | null;
  refill: {
    medication: string | null;
    notes: string | null;
    pharmacy?: string | null;
    urgency?: string | null;
  };
  refill_complete?: boolean;
  voice_handoff: unknown;
  voice_handoff_ready?: boolean;
  voice_handoff_at?: string | null;
  messages: { role: string; content: string }[];
  office: Record<string, unknown>;
  match_error?: string | null;
};

export type UiHints = {
  show_intake: boolean;
  show_provider: boolean;
  show_slots: boolean;
  match_error?: string | null;
};
