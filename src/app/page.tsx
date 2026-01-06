"use client";

import { AppShell } from "@/components/shell";
import { Silk } from "@/components/ui/silk";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Animated Silk Background */}
      <div className="absolute inset-0">
        <Silk
          speed={1.7}
          scale={1}
          color="#260245"
          noiseIntensity={0.9}
          rotation={0}
        />
      </div>

      {/* Blueprint Builder App */}
      <div className="relative z-10 flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-2xl h-[90vh] rounded-2xl overflow-hidden shadow-2xl bg-background/95 backdrop-blur-sm">
          <AppShell />
        </div>
      </div>
    </div>
  );
}
