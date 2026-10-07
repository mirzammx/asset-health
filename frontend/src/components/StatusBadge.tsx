import type { Status } from "@/api/client";
import { STATUS_LABEL, STATUS_PILL } from "@/lib/status";

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${STATUS_PILL[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
