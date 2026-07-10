import OurStory from "@/components/OurStory";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hikayemiz | EcoTrace",
  description:
    "Yazılım dünyasının görünmez karbon ayak izi ve EcoTrace'in bu sorunu çözme misyonu.",
};

export default function StoryPage() {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#050806]">
      <SiteHeader />
      <main className="flex-1">
        <OurStory />
      </main>
      <SiteFooter />
    </div>
  );
}
