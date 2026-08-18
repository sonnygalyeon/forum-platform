"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  useEffect(() => {
    const saved = localStorage.getItem("night-iris-theme") as "dark" | "light" | null;
    const initial = saved ?? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    setTheme(initial);
    document.documentElement.dataset.theme = initial;
  }, []);

  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("night-iris-theme", next);
    document.documentElement.dataset.theme = next;
  }

  return <button className="icon-button" onClick={toggle} aria-label="Сменить тему">{theme === "dark" ? <Sun size={17}/> : <Moon size={17}/>}</button>;
}
