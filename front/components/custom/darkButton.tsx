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
    return (
      <div className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-200 dark:bg-gray-700"></div>
    );
  }

  const currentIcon =
    resolvedTheme === "dark" ? (
      <Sun size={24} className="text-yellow-500" />
    ) : (
      <Moon size={24} strokeWidth={2} className="text-gray-700" />
    );

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full flex items-center justify-center transition-colors bg-[--bg-light] hover:bg-[--bg-light] dark:hover:bg-[--bg-light]"
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
      <span className="sr-only">Theme switcher button</span>
    </button>
  );
}
