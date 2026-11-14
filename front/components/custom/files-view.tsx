"use client";

import {
  ChevronLeft,
  Download,
  FileText,
  Folder,
  FolderPlus,
  MoreHorizontal,
  Star,
  StarOff,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";

import { DataTable, type DataTableColumn } from "@/components/custom/data-table";
import { FileCategoryList, type FileView } from "@/components/custom/file-category-list";
import { SearchBar } from "@/components/custom/search-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUrlSearch } from "@/hooks/use-url-search";
import { createFolder, deleteStorageNode, setFavourite } from "@/lib/actions";
import type { ActionResult } from "@/lib/api";
import { formatBytes, formatRelativeFromNow } from "@/lib/format";
import type { StorageNode } from "@/lib/types";

const trim = (p: string) => p.replace(/^\/+|\/+$/g, "");

function parentOf(path: string) {
  const parts = trim(path).split("/");
  parts.pop();
  return parts.join("/");
}

export function FilesView({
  view,
  path,
  searching,
  nodes,
  error,
}: {
  view: FileView;
  path: string;
  searching: boolean;
  nodes: StorageNode[] | null;
  error: string | null;
}) {
  const search = useUrlSearch();
  const [pending, startTransition] = useTransition();
  const [actionError, setActionError] = useState<string | null>(null);

  function run(action: () => Promise<ActionResult>) {
    setActionError(null);
    startTransition(async () => {
      const res = await action();
      if (!res.ok) setActionError(res.error);
    });
  }

  function onNewFolder() {
    const name = window.prompt("Nom du nouveau dossier")?.trim();
    if (!name) return;
    run(() => createFolder([trim(path), name].filter(Boolean).join("/")));
  }

  const columns: DataTableColumn<StorageNode>[] = [
    {
      key: "name",
      header: "Nom",
      render: (row) => (
        <div className="flex items-center gap-2">
          {row.is_dir ? (
            <Folder className="size-4 text-muted-foreground" />
          ) : (
            <FileText className="size-4 text-muted-foreground" />
          )}
          {row.is_dir ? (
            <Link
              href={`/file?${new URLSearchParams({ path: trim(row.path) })}`}
              className="truncate hover:underline"
            >
              {row.name}
            </Link>
          ) : (
            <span className="truncate">{row.name}</span>
          )}
        </div>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (row) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Options" disabled={pending}>
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {!row.is_dir && (
              <DropdownMenuItem asChild>
                <a href={`/api/storage/download?${new URLSearchParams({ path: row.path })}`}>
                  <Download className="mr-2 size-4" />
                  Télécharger
                </a>
              </DropdownMenuItem>
            )}
            {view === "favourites" ? (
              <DropdownMenuItem onSelect={() => run(() => setFavourite(row.path, false))}>
                <StarOff className="mr-2 size-4" />
                Retirer des favoris
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onSelect={() => run(() => setFavourite(row.path, true))}>
                <Star className="mr-2 size-4" />
                Ajouter aux favoris
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-brand-red focus:text-brand-red"
              onSelect={() => {
                if (window.confirm(`Supprimer « ${row.name} » ?`)) {
                  run(() => deleteStorageNode(row.path));
                }
              }}
            >
              <Trash2 className="mr-2 size-4" />
              Supprimer
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
      className: "w-16 text-right",
      headerClassName: "w-16",
    },
    {
      key: "size",
      header: "Taille",
      render: (row) => <span className="tabular-nums">{formatBytes(row.size)}</span>,
      className: "w-24 text-right tabular-nums",
      headerClassName: "w-24 text-right",
    },
    {
      key: "modified",
      header: "Modifié",
      render: (row) => (
        <span className="text-muted-foreground">
          {formatRelativeFromNow(new Date(row.last_modified))}
        </span>
      ),
      className: "w-40",
      headerClassName: "w-40",
    },
  ];

  const list = nodes ?? [];
  const totalBytes = list.reduce((s, f) => s + f.size, 0);
  const foldersCount = list.filter((f) => f.is_dir).length;
  const current = trim(path);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <SearchBar
        value={search.value}
        onChange={search.setValue}
        placeholder="Rechercher un fichier (* pour joker)"
      />

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-[minmax(0,240px)_minmax(0,1fr)]">
        <Card className="h-full">
          <CardContent className="p-3">
            <FileCategoryList active={view} />
          </CardContent>
        </Card>

        <Card className="h-full min-h-0">
          <CardContent className="flex h-full flex-col p-0">
            <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-2 text-sm">
              <div className="flex min-w-0 items-center gap-2">
                {view === "all" && !searching && current && (
                  <Button asChild variant="ghost" size="icon-sm" aria-label="Dossier parent">
                    <Link
                      href={
                        parentOf(current)
                          ? `/file?${new URLSearchParams({ path: parentOf(current) })}`
                          : "/file"
                      }
                    >
                      <ChevronLeft />
                    </Link>
                  </Button>
                )}
                <span className="truncate font-medium">
                  {searching
                    ? "Résultats de recherche"
                    : view === "favourites"
                      ? "Favoris"
                      : `/${current}`}
                </span>
              </div>
              {view === "all" && !searching && (
                <Button variant="outline" size="sm" onClick={onNewFolder} disabled={pending}>
                  <FolderPlus />
                  Nouveau dossier
                </Button>
              )}
            </div>
            {actionError && (
              <p className="border-b border-border px-4 py-2 text-sm text-destructive">
                {actionError}
              </p>
            )}
            <div className="flex-1 overflow-y-auto">
              {error ? (
                <p className="p-4 text-sm text-destructive">{error}</p>
              ) : (
                <DataTable
                  columns={columns}
                  data={list}
                  rowKey={(r) => r.file_id || r.path}
                  emptyMessage="Aucun fichier."
                />
              )}
            </div>
            <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
              <span>
                {list.length - foldersCount} fichiers – {foldersCount} dossiers
              </span>
              <span>{formatBytes(totalBytes)}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
