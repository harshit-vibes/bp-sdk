import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-4">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
        <h2 className="text-2xl font-semibold">Page not found</h2>
        <p className="max-w-md text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </div>
      <div className="flex gap-4">
        <Button asChild variant="default">
          <Link href="/">
            <Home className="mr-2 h-4 w-4" />
            Go home
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="javascript:history.back()">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Go back
          </Link>
        </Button>
      </div>
    </div>
  );
}
