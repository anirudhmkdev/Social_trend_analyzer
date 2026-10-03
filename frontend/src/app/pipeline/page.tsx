import { redirect } from "next/navigation";
export default async function LegacyPage({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const query = new URLSearchParams(await searchParams);
  redirect(`/analysis?${query}`);
}
