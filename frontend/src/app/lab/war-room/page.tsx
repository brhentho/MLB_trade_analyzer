import type { Metadata } from "next";
import { WarRoom } from "@/components/war-room/WarRoom";

export const metadata: Metadata = {
  title: "Diamond war room · StatSlugger",
};

export default function WarRoomPage() {
  return <WarRoom />;
}
