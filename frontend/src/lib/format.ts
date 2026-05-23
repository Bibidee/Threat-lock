/** Format an ISO/epoch/Date value as a fixed UTC string, e.g. "23 May 2026, 14:30:18 UTC".
 *  All dashboard timestamps use this so they read the same regardless of the viewer's timezone. */
export function formatUtc(value: string | number | Date | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return (
    d.toLocaleString("en-GB", {
      timeZone: "UTC",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }) + " UTC"
  );
}
