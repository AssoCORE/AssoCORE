"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";

/**
 * A search box whose value lives in the URL (`?q=`), so the Server Component
 * re-fetches with the backend doing the filtering. Debounced to avoid one
 * request per keystroke.
 */
export function useUrlSearch(param = "q", delayMs = 300) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [value, setValue] = useState(searchParams.get(param) ?? "");
  const [pending, startTransition] = useTransition();
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    const id = setTimeout(() => {
      const next = new URLSearchParams(searchParams.toString());
      if (value.trim()) next.set(param, value.trim());
      else next.delete(param);
      const qs = next.toString();
      startTransition(() => router.replace(qs ? `${pathname}?${qs}` : pathname));
    }, delayMs);
    return () => clearTimeout(id);
    // searchParams is intentionally omitted: re-running on our own replace() would loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return { value, setValue, pending };
}

/**
 * A single URL query param (e.g. a filter choice) the Server Component reads.
 * Setting it to `fallback` removes it, so the default state keeps a clean URL.
 */
export function useUrlParam(param: string, fallback = "") {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();
  const value = searchParams.get(param) ?? fallback;

  function setValue(next: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (next && next !== fallback) params.set(param, next);
    else params.delete(param);
    const qs = params.toString();
    startTransition(() => router.replace(qs ? `${pathname}?${qs}` : pathname));
  }

  return { value, setValue, pending };
}
