"use client";

import { AppShell } from "@/components/shell";
import { Silk } from "@/components/ui/silk";

export default function Home() {
  return (
    <div className="relative min-h-dvh w-full overflow-hidden">
      {/* Animated Silk Background - hidden on mobile for performance */}
      <div className="absolute inset-0 hidden sm:block">
        <Silk
          speed={1.7}
          scale={1}
          color="#260245"
          noiseIntensity={0.9}
          rotation={0}
        />
      </div>

      {/* Mobile: Full viewport with solid background */}
      {/* Desktop: Centered card with backdrop blur */}
      <div className="relative z-10 flex min-h-dvh w-full items-center justify-center p-0 sm:p-4">
        <div className="w-full h-dvh sm:h-[90vh] sm:max-w-2xl sm:rounded-2xl overflow-hidden sm:shadow-2xl bg-background sm:bg-background/95 sm:backdrop-blur-sm">
          <AppShell />
        </div>
      </div>
    </div>
  );
}
