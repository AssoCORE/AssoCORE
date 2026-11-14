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
