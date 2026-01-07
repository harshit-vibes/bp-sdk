"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Key, Building2, ArrowRight, Check, AlertCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

// Cookie names
const COOKIE_NAMES = {
  API_KEY: "bp_builder_api_key",
  BEARER_TOKEN: "bp_builder_bearer_token",
  ORG_ID: "bp_builder_org_id",
};

// Cookie max age in days
const COOKIE_MAX_AGE_DAYS = 30;

export interface ApiCredentials {
  apiKey: string;
  bearerToken: string;
  orgId: string;
}

export interface SetupScreenProps {
  /** Callback when setup is complete */
  onComplete: (credentials: ApiCredentials) => void;
  /** Additional class names */
  className?: string;
}

// Helper to get cookie value
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

// Helper to set cookie
function setCookie(name: string, value: string, days: number = COOKIE_MAX_AGE_DAYS): void {
  if (typeof document === "undefined") return;
  const maxAge = days * 24 * 60 * 60;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Strict`;
}

// Parse JWT to get expiration time
function parseJwtExpiration(token: string): Date | null {
  try {
    // JWT format: header.payload.signature
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = JSON.parse(atob(parts[1]));
    if (payload.exp) {
      return new Date(payload.exp * 1000);
    }
    return null;
  } catch {
    return null;
  }
}

// Format time remaining
function formatTimeRemaining(expirationDate: Date): string {
  const now = new Date();
  const diff = expirationDate.getTime() - now.getTime();

  if (diff <= 0) return "Expired";

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (days > 0) return `${days}d ${hours}h remaining`;
  if (hours > 0) return `${hours}h ${minutes}m remaining`;
  return `${minutes}m remaining`;
}

/**
 * SetupScreen - Welcome screen for API key configuration
 *
 * Allows users to input their Lyzr API credentials before starting
 * the blueprint building process.
 */
export function SetupScreen({ onComplete, className }: SetupScreenProps) {
  const [apiKey, setApiKey] = useState("");
  const [bearerToken, setBearerToken] = useState("");
  const [orgId, setOrgId] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [showBearerToken, setShowBearerToken] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRemaining, setTimeRemaining] = useState<string | null>(null);

  // Parse token expiration
  const tokenExpiration = useMemo(() => {
    if (!bearerToken) return null;
    return parseJwtExpiration(bearerToken);
  }, [bearerToken]);

  const isTokenValid = useMemo(() => {
    if (!tokenExpiration) return null; // Unknown (not a JWT)
    return tokenExpiration.getTime() > Date.now();
  }, [tokenExpiration]);

  // Update countdown timer
  useEffect(() => {
    if (!tokenExpiration) {
      setTimeRemaining(null);
      return;
    }

    const updateTimer = () => {
      setTimeRemaining(formatTimeRemaining(tokenExpiration));
    };

    updateTimer();
    const interval = setInterval(updateTimer, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [tokenExpiration]);

  // Load saved credentials from cookies on mount
  useEffect(() => {
    const savedApiKey = getCookie(COOKIE_NAMES.API_KEY) || "";
    const savedBearerToken = getCookie(COOKIE_NAMES.BEARER_TOKEN) || "";
    const savedOrgId = getCookie(COOKIE_NAMES.ORG_ID) || "";

    setApiKey(savedApiKey);
    setBearerToken(savedBearerToken);
    setOrgId(savedOrgId);
    setIsLoading(false);

    // Auto-continue if all credentials are saved
    if (savedApiKey && savedBearerToken && savedOrgId) {
      onComplete({
        apiKey: savedApiKey,
        bearerToken: savedBearerToken,
        orgId: savedOrgId,
      });
    }
  }, [onComplete]);

  const handleSubmit = useCallback(() => {
    if (!apiKey || !bearerToken || !orgId) return;

    // Save to cookies
    setCookie(COOKIE_NAMES.API_KEY, apiKey);
    setCookie(COOKIE_NAMES.BEARER_TOKEN, bearerToken);
    setCookie(COOKIE_NAMES.ORG_ID, orgId);

    onComplete({ apiKey, bearerToken, orgId });
  }, [apiKey, bearerToken, orgId, onComplete]);

  const isValid = apiKey.trim() && bearerToken.trim() && orgId.trim();

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center h-full", className)}>
        <div className="text-muted-foreground text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex-1 overflow-y-auto p-6">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 text-white mb-4">
            <Key className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Welcome to Blueprint Builder</h1>
          <p className="text-muted-foreground text-sm max-w-sm mx-auto">
            Enter your Lyzr API credentials to get started. These are securely stored in your browser.
          </p>
        </div>

        {/* Credentials Form */}
        <div className="space-y-4 max-w-sm mx-auto">
          {/* API Key */}
          <div className="space-y-2">
            <Label htmlFor="api-key" className="flex items-center gap-2 text-sm">
              <Key className="h-3.5 w-3.5 text-orange-500" />
              Lyzr API Key
            </Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="lyzr-api-xxx..."
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              Go to <a href="https://studio.lyzr.ai/account/" target="_blank" rel="noopener noreferrer" className="text-orange-500 hover:underline">studio.lyzr.ai/account</a> and click &quot;Copy API Key&quot;
            </p>
          </div>

          {/* Bearer Token */}
          <div className="space-y-2">
            <Label htmlFor="bearer-token" className="flex items-center gap-2 text-sm">
              <Key className="h-3.5 w-3.5 text-orange-500" />
              Blueprint Bearer Token
            </Label>
            <div className="relative">
              <Input
                id="bearer-token"
                type={showBearerToken ? "text" : "password"}
                value={bearerToken}
                onChange={(e) => setBearerToken(e.target.value)}
                placeholder="Bearer token..."
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowBearerToken(!showBearerToken)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showBearerToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {/* Token validity indicator */}
            {bearerToken && (
              <div className="flex items-center gap-2 text-xs">
                {isTokenValid === true && (
                  <>
                    <Check className="h-3 w-3 text-green-600" />
                    <span className="text-green-600">Valid</span>
                    {timeRemaining && (
                      <>
                        <Clock className="h-3 w-3 text-muted-foreground ml-2" />
                        <span className="text-muted-foreground">{timeRemaining}</span>
                      </>
                    )}
                  </>
                )}
                {isTokenValid === false && (
                  <>
                    <AlertCircle className="h-3 w-3 text-destructive" />
                    <span className="text-destructive">Token expired</span>
                  </>
                )}
                {isTokenValid === null && (
                  <span className="text-muted-foreground">Token format not recognized</span>
                )}
              </div>
            )}
            {!bearerToken && (
              <p className="text-xs text-muted-foreground">
                Open DevTools → Network → find &quot;by_organisation&quot; request → copy from Authorization header
              </p>
            )}
          </div>

          {/* Organization ID */}
          <div className="space-y-2">
            <Label htmlFor="org-id" className="flex items-center gap-2 text-sm">
              <Building2 className="h-3.5 w-3.5 text-orange-500" />
              Organization ID
            </Label>
            <Input
              id="org-id"
              type="text"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              placeholder="org_xxx..."
            />
            <p className="text-xs text-muted-foreground">
              From same Network request → check payload for organisation-id
            </p>
          </div>

          {/* Status indicators */}
          <div className="pt-4 flex items-center gap-4 justify-center">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
              apiKey ? "bg-green-100 dark:bg-green-900" : "bg-muted"
            )}>
              {apiKey ? (
                <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <Key className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
              bearerToken ? (isTokenValid === false ? "bg-red-100 dark:bg-red-900" : "bg-green-100 dark:bg-green-900") : "bg-muted"
            )}>
              {bearerToken ? (
                isTokenValid === false ? (
                  <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                ) : (
                  <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                )
              ) : (
                <Key className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
              orgId ? "bg-green-100 dark:bg-green-900" : "bg-muted"
            )}>
              {orgId ? (
                <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <Building2 className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t">
        <Button
          onClick={handleSubmit}
          disabled={!isValid}
          className="w-full bg-orange-500 hover:bg-orange-600"
        >
          Continue to Builder
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

/**
 * Get stored credentials from cookies
 */
export function getStoredCredentials(): ApiCredentials | null {
  if (typeof window === "undefined") return null;

  const apiKey = getCookie(COOKIE_NAMES.API_KEY);
  const bearerToken = getCookie(COOKIE_NAMES.BEARER_TOKEN);
  const orgId = getCookie(COOKIE_NAMES.ORG_ID);

  if (!apiKey || !bearerToken || !orgId) return null;

  return { apiKey, bearerToken, orgId };
}

/**
 * Clear stored credentials
 */
export function clearStoredCredentials(): void {
  if (typeof document === "undefined") return;

  // Set cookies with max-age=0 to delete them
  document.cookie = `${COOKIE_NAMES.API_KEY}=; path=/; max-age=0`;
  document.cookie = `${COOKIE_NAMES.BEARER_TOKEN}=; path=/; max-age=0`;
  document.cookie = `${COOKIE_NAMES.ORG_ID}=; path=/; max-age=0`;
}
