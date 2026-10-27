"use client";

import { FileText, Folder, MoreHorizontal, UserPlus } from "lucide-react";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/custom/data-table";
import { FileCategoryList } from "@/components/custom/file-category-list";
import { SearchBar } from "@/components/custom/search-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { fileCategories, files } from "@/lib/mock/files";
import { formatBytes, formatRelativeFromNow } from "@/lib/format";
import type { FileCategory, FileNode } from "@/lib/types";

const columns: DataTableColumn<FileNode>[] = [
  {
    key: "select",
    header: <Checkbox aria-label="Tout sélectionner" />,
    render: (row) => <Checkbox aria-label={`Sélectionner ${row.name}`} />,
    className: "w-8",
    headerClassName: "w-8",
  },
  {
    key: "name",
    header: "Nom",
    render: (row) => (
      <div className="flex items-center gap-2">
        {row.kind === "folder" ? (
          <Folder className="size-4 text-muted-foreground" />
        ) : (
          <FileText className="size-4 text-muted-foreground" />
        )}
        <span className="truncate">{row.name}</span>
      </div>
    ),
  },
  {
    key: "actions",
    header: "",
    render: () => (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Button variant="ghost" size="icon" aria-label="Partager">
          <UserPlus className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Options">
          <MoreHorizontal className="size-4" />
        </Button>
      </div>
    ),
    className: "w-24 text-right",
    headerClassName: "w-24",
  },
  {
    key: "size",
    header: "Taille",
    render: (row) => <span className="tabular-nums">{formatBytes(row.sizeBytes)}</span>,
    className: "w-24 text-right tabular-nums",
    headerClassName: "w-24 text-right",
  },
  {
    key: "modified",
    header: "Modifié",
    render: (row) => (
      <span className="text-muted-foreground">{formatRelativeFromNow(row.modifiedAt)}</span>
    ),
    className: "w-40",
    headerClassName: "w-40",
  },
];

export default function FilePage() {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<FileCategory>("Tous les fichiers");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return files;
    return files.filter((f) => f.name.toLowerCase().includes(q));
  }, [query]);

  const totalBytes = files.reduce((s, f) => s + f.sizeBytes, 0);
  const foldersCount = files.filter((f) => f.kind === "folder").length;

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <SearchBar
        value={query}
        onChange={setQuery}
        placeholder="Search a file (Ctrl+/)"
      />

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,240px)_minmax(0,1fr)]">
        <Card className="h-full">
          <CardContent className="p-3">
            <FileCategoryList
              categories={fileCategories}
              active={active}
              onSelect={setActive}
            />
          </CardContent>
        </Card>

        <Card className="h-full min-h-0">
          <CardContent className="flex h-full flex-col p-0">
            <div className="flex-1 overflow-y-auto">
              <DataTable columns={columns} data={filtered} rowKey={(r) => r.id} />
            </div>
            <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
              <span>
                {files.length} fichiers – {foldersCount} Dossiers
              </span>
              <span>{formatBytes(totalBytes)}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
