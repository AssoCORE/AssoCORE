"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function DarkButton() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  if (!mounted) {
    return <div className="w-10 h-10" />;
  }

  const currentIcon =
    resolvedTheme === "light" ? (
      <Sun size={24} className="text-gray-500" />
    ) : (
      <Moon size={24} strokeWidth={2} className="text-golden-700" />
    );

  return (
    <button
      onClick={toggleTheme}
      className="px-4 py-2 text-white rounded"
      aria-label={
        resolvedTheme === "dark"
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
      title={
        resolvedTheme === "dark"
          ? "Switch to light theme"
          : "Switch to dark theme"
      }
    >
      {currentIcon}
      <span className="sr-only">Day/Night switch button</span>
    </button>
  );
}
