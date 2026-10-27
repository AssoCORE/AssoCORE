"use client";

import { useState, type ReactNode } from "react";
import { AdminContext } from "@/hooks/use-admin";

export function AdminProvider({
  children,
  defaultValue = false,
}: {
  children: ReactNode;
  defaultValue?: boolean;
}) {
  const [isAdmin, setIsAdmin] = useState(defaultValue);
  return (
    <AdminContext.Provider value={{ isAdmin, setIsAdmin }}>
      {children}
    </AdminContext.Provider>
  );
}
