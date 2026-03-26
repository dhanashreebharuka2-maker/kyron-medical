"use client";

import type { ComponentProps } from "react";
import { AppointmentSlotPicker } from "./AppointmentSlotPicker";

type Props = ComponentProps<typeof AppointmentSlotPicker>;

/** Slot picker styled for the in-chat scheduling flow */
export function SlotPickerCard(props: Props) {
  return <AppointmentSlotPicker embedded {...props} />;
}
