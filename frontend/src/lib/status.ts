import type { Status } from "@/api/client";

export const STATUS_LABEL: Record<Status, string> = {
  normal: "Normal", degrading: "Degrading", attention: "Attention", unknown: "No data",
};

// Full class names so Tailwind can see them.
export const STATUS_TEXT: Record<Status, string> = {
  normal: "text-ok", degrading: "text-warn", attention: "text-bad", unknown: "text-muted-foreground",
};
export const STATUS_PILL: Record<Status, string> = {
  normal: "bg-ok/15 text-ok", degrading: "bg-warn/15 text-warn",
  attention: "bg-bad/15 text-bad", unknown: "bg-muted text-muted-foreground",
};
export const STATUS_HEX: Record<Status, string> = {
  normal: "#34d399", degrading: "#fbbf24", attention: "#fb497a", unknown: "#737373",
};
