"use client";

import { motion } from "framer-motion";

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

type Props = { office: Office; embedded?: boolean };

const WEEK_ORDER = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const;

function hoursRows(hours: Record<string, string>): [string, string][] {
  const primary = WEEK_ORDER.filter((d) => d in hours).map((d) => [d, hours[d]] as [string, string]);
  const rest = Object.entries(hours).filter(([d]) => !WEEK_ORDER.includes(d as (typeof WEEK_ORDER)[number]));
  return [...primary, ...rest];
}

export function OfficeInfoCard({ office, embedded }: Props) {
  const rows = hoursRows(office.hours);
  const tel = office.phone.replace(/\D/g, "");
  // Sidebar column is narrow (~1/3 of max width); side‑by‑side address + hours clips the hours table.
  const mainGrid = embedded
    ? "mt-4 grid gap-6 sm:grid-cols-2 sm:gap-8 sm:items-start"
    : "mt-4 grid grid-cols-1 gap-6 sm:items-start";
  const hoursShell = embedded
    ? "min-w-0 border-t border-slate-200/70 pt-4 sm:border-l sm:border-t-0 sm:pl-8 sm:pt-0"
    : "min-w-0 border-t border-slate-200/70 pt-4";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={
        embedded
          ? "rounded-2xl border border-kyron-200/60 bg-white/85 p-4 shadow-inner backdrop-blur-xl"
          : "rounded-2xl border border-white/50 bg-white/55 p-5 shadow-glass backdrop-blur-2xl sm:p-6"
      }
    >
      <h3 className="font-display text-base font-semibold tracking-tight text-ink sm:text-lg">{office.name}</h3>
      <div className={mainGrid}>
        <div className="min-w-0 space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Address & contact</p>
          <p className="text-sm leading-relaxed text-slate-700">
            {office.address_line1}
            {office.address_line2 ? (
              <>
                <br />
                {office.address_line2}
              </>
            ) : null}
            <br />
            {office.city}, {office.state} {office.zip}
          </p>
          <p className="text-sm">
            <span className="text-slate-500">Phone </span>
            <a className="font-medium text-kyron-700 hover:underline" href={tel ? `tel:${tel}` : undefined}>
              {office.phone}
            </a>
          </p>
          {office.parking && (
            <p className="border-t border-slate-200/80 pt-3 text-xs leading-relaxed text-slate-600">{office.parking}</p>
          )}
        </div>
        <div className={hoursShell}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Hours</p>
          <div className="mt-3 min-w-0 overflow-x-auto [-webkit-overflow-scrolling:touch]">
            <table className="w-full border-collapse text-sm">
              <tbody>
                {rows.map(([day, time]) => (
                  <tr key={day}>
                    <th
                      scope="row"
                      className="w-[1%] py-1.5 pr-3 text-left align-top font-normal capitalize text-slate-600"
                    >
                      {day}
                    </th>
                    <td className="min-w-0 py-1.5 text-right tabular-nums text-slate-800 whitespace-nowrap">
                      {time}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
