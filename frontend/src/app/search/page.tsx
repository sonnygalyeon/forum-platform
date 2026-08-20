import { Suspense } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SearchExperience } from "@/components/search/search-experience";
import { LoadingBlock } from "@/components/ui/loading";

export default function SearchPage() {
  return <AppShell><Suspense fallback={<LoadingBlock/>}><SearchExperience/></Suspense></AppShell>;
}
