import type { FileView } from "@/components/custom/file-category-list";
import { FilesView } from "@/components/custom/files-view";
import { apiJson, query } from "@/lib/api";
import { BackendError } from "@/lib/backend";
import type { StorageNode } from "@/lib/types";

export default async function FilePage({
  searchParams,
}: {
  searchParams: Promise<{ view?: string; path?: string; q?: string }>;
}) {
  const params = await searchParams;
  const view: FileView = params.view === "favourites" ? "favourites" : "all";
  const path = params.path ?? "";
  const q = params.q?.trim() ?? "";

  const url = q
    ? `/storage/search${query({ q, path })}`
    : view === "favourites"
      ? "/storage/favourites"
      : `/storage/${query({ path })}`;

  let nodes: StorageNode[] | null = null;
  let error: string | null = null;
  try {
    nodes = await apiJson<StorageNode[]>(url);
  } catch (err) {
    error =
      err instanceof BackendError && err.status !== 503
        ? err.detail
        : "Le stockage Nextcloud est indisponible pour le moment.";
  }

  return (
    <FilesView
      view={view}
      path={path}
      searching={!!q}
      nodes={nodes}
      error={error}
    />
  );
}
