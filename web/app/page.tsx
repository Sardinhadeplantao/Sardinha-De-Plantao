import { loadData, slim } from "@/lib/server-data";
import { Dashboard } from "@/components/Dashboard";

export default function Home() {
  return <Dashboard data={slim(loadData())} />;
}
