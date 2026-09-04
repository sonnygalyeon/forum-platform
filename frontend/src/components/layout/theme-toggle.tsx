"use client";

import { Moon, Sun } from "lucide-react";
import {
  useEffect,
  useSyncExternalStore,
} from "react";

type Theme = "dark" | "light";

const STORAGE_KEY = "night-iris-theme";
const THEME_EVENT = "night-iris-theme-change";

function preferredTheme(): Theme {
  if (typeof window === "undefined") return "dark";

  const saved =
    window.localStorage.getItem(STORAGE_KEY);

  if (saved === "dark" || saved === "light") {
    return saved;
  }

  return window.matchMedia(
    "(prefers-color-scheme: light)",
  ).matches
    ? "light"
    : "dark";
}

function getThemeSnapshot(): Theme {
  if (typeof document === "undefined") {
    return "dark";
  }

  const current =
    document.documentElement.dataset.theme;

  if (current === "dark" || current === "light") {
    return current;
  }

  return preferredTheme();
}

function subscribeTheme(callback: () => void) {
  const media = window.matchMedia(
    "(prefers-color-scheme: light)",
  );

  const notify = () => callback();

  window.addEventListener(THEME_EVENT, notify);
  window.addEventListener("storage", notify);
  media.addEventListener("change", notify);

  return () => {
    window.removeEventListener(THEME_EVENT, notify);
    window.removeEventListener("storage", notify);
    media.removeEventListener("change", notify);
  };
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(
    subscribeTheme,
    getThemeSnapshot,
    () => "dark",
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function toggle() {
    const next: Theme =
      theme === "dark" ? "light" : "dark";

    window.localStorage.setItem(STORAGE_KEY, next);
    document.documentElement.dataset.theme = next;
    window.dispatchEvent(new Event(THEME_EVENT));
  }

  return (
    <button
      className="icon-button"
      onClick={toggle}
      aria-label="Сменить тему"
    >
      {theme === "dark" ? (
        <Sun size={17} />
      ) : (
        <Moon size={17} />
      )}
    </button>
  );
}
