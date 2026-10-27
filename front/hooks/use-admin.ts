"use client";

import { createContext, useContext } from "react";

type AdminCtx = {
  isAdmin: boolean;
  setIsAdmin: (value: boolean) => void;
};

export const AdminContext = createContext<AdminCtx | null>(null);

export function useAdmin() {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error("useAdmin must be used inside <AdminProvider>");
  return ctx;
}
