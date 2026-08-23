import { HomeShell } from "@/components/home-shell";
import { redirect } from "next/navigation";

export default async function ResearchPage(props: PageProps<"/research">) {
  const searchParams = await props.searchParams;
  const projectId = typeof searchParams.project === "string" ? searchParams.project.trim() : "";
  if (projectId) redirect(`/projects/${encodeURIComponent(projectId)}`);
  return <HomeShell />;
}
