"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-4">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="rounded-full bg-destructive/10 p-4">
          <AlertCircle className="h-10 w-10 text-destructive" />
        </div>
        <h1 className="text-2xl font-semibold">Something went wrong</h1>
        <p className="max-w-md text-muted-foreground">
          An unexpected error occurred. Please try again or contact support if the problem persists.
        </p>
        {error.digest && (
          <p className="text-xs text-muted-foreground">
            Error ID: {error.digest}
          </p>
        )}
      </div>
      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          <RefreshCw className="mr-2 h-4 w-4" />
          Try again
        </Button>
        <Button onClick={() => window.location.href = "/"} variant="outline">
          Go home
        </Button>
      </div>
    </div>
  );
}
