import type { Metadata } from "next";
import { ScoutingReport } from "@/components/scouting-report/ScoutingReport";

export const metadata: Metadata = {
  title: "Scouting report · StatSlugger",
};

export default function ScoutingReportPage() {
  return <ScoutingReport />;
}
