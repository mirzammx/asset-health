import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fetchAssets } from "@/api/client";
import { StatusBadge } from "@/components/StatusBadge";
import { usePolling } from "@/hooks/usePolling";

export function Assets({ query }: { query: string }) {
  const { data, error } = usePolling(fetchAssets, []);
  const [pageSize, setPageSize] = useState(5);
  const [page, setPage] = useState(0);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data ?? []).filter((a) => !q || `${a.name} ${a.type} ${a.status}`.toLowerCase().includes(q));
  }, [data, query]);

  useEffect(() => setPage(0), [query, pageSize]);
  const pages = Math.max(1, Math.ceil(rows.length / pageSize));
  const slice = rows.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Assets</h1>
        <p className="text-muted-foreground">All monitored equipment. Use the search box above to filter.</p>
      </div>
      {error && <p className="text-bad">Cannot reach API: {error}</p>}
      <Card className="p-0">
        <div className="flex items-center gap-2 border-b px-4 py-3 text-sm">
          <span className="text-muted-foreground">Show</span>
          <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}
                  className="rounded-md border bg-transparent px-2 py-1">
            {[5, 10, 25].map((n) => <option key={n} value={n} className="bg-card">{n}</option>)}
          </select>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="pl-4">Asset</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Health</TableHead>
              <TableHead className="pr-4 text-right">Last updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {slice.map((a) => (
              <TableRow key={a.id} className="cursor-pointer" onClick={() => (window.location.hash = `#/assets/${a.id}`)}>
                <TableCell className="pl-4 font-medium">{a.name}</TableCell>
                <TableCell className="capitalize text-muted-foreground">{a.type}</TableCell>
                <TableCell><StatusBadge status={a.status} /></TableCell>
                <TableCell className="text-right">{a.health_index != null ? `${Math.round(a.health_index)}%` : "—"}</TableCell>
                <TableCell className="pr-4 text-right text-muted-foreground">
                  {a.as_of ? new Date(a.as_of).toLocaleTimeString() : "—"}
                </TableCell>
              </TableRow>
            ))}
            {data && slice.length === 0 && (
              <TableRow><TableCell colSpan={5} className="py-8 text-center text-muted-foreground">No assets match.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <div className="flex items-center justify-between border-t px-4 py-3 text-sm text-muted-foreground">
          <span>Showing {rows.length === 0 ? 0 : page * pageSize + 1} to {Math.min((page + 1) * pageSize, rows.length)} of {rows.length}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
            <Button variant="outline" size="sm" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
