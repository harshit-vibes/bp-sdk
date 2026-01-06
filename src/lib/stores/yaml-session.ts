/**
 * YAML Session Store
 *
 * In-memory storage for YAML files during a builder session.
 * Stores files at virtual paths like:
 * - /blueprints/local/agents/{filename}.yaml
 * - /blueprints/local/blueprints/{filename}.yaml
 *
 * Session-scoped: cleared on page refresh or explicit reset.
 */

import { useCallback, useSyncExternalStore } from "react";
import type { AgentYAMLSpec } from "@/lib/types";
import {
  generateAgentYAML,
  generateBlueprintYAML,
  slugify,
  getAgentFilename,
} from "@/lib/yaml";

// Module-level storage (session-scoped)
let files: Record<string, string> = {};
let listeners: Set<() => void> = new Set();

// Notify all subscribers when files change
function emitChange() {
  listeners.forEach((listener) => listener());
}

// Subscribe to store changes
function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Get current snapshot
function getSnapshot(): Record<string, string> {
  return files;
}

// Server-side snapshot (empty)
function getServerSnapshot(): Record<string, string> {
  return {};
}

/**
 * Save an agent YAML to the session store
 *
 * @param agent - Agent specification to save
 * @param allSpecs - Optional: all agent specs (for computing sub_agents on managers)
 */
export function saveAgentToSession(
  agent: AgentYAMLSpec,
  allSpecs?: AgentYAMLSpec[]
): string {
  const filename = getAgentFilename(agent);  // Use consistent filename helper
  const path = `/blueprints/local/agents/${filename}`;
  const content = generateAgentYAML(agent, allSpecs);

  files = { ...files, [path]: content };
  emitChange();

  return path;
}

/**
 * Save a blueprint YAML to the session store
 */
export function saveBlueprintToSession(
  name: string,
  description: string,
  agentSpecs: AgentYAMLSpec[],
  options?: {
    category?: string;
    tags?: string[];
    visibility?: string;
  }
): string {
  const filename = `${slugify(name)}.yaml`;
  const path = `/blueprints/local/blueprints/${filename}`;
  const content = generateBlueprintYAML(name, description, agentSpecs, options);

  files = { ...files, [path]: content };
  emitChange();

  return path;
}

/**
 * Get a file from the session store
 */
export function getFileFromSession(path: string): string | null {
  return files[path] || null;
}

/**
 * List all agent YAML paths
 */
export function listAgentPaths(): string[] {
  return Object.keys(files).filter((p) =>
    p.startsWith("/blueprints/local/agents/")
  );
}

/**
 * List all blueprint YAML paths
 */
export function listBlueprintPaths(): string[] {
  return Object.keys(files).filter((p) =>
    p.startsWith("/blueprints/local/blueprints/")
  );
}

/**
 * Clear all files from the session store
 */
export function clearSession(): void {
  files = {};
  emitChange();
}

/**
 * Get total file count
 */
export function getFileCount(): number {
  return Object.keys(files).length;
}

/**
 * React hook to access YAML session store with reactivity
 */
export function useYAMLSession() {
  // Subscribe to store changes using React 18's useSyncExternalStore
  const currentFiles = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );

  const agentPaths = Object.keys(currentFiles).filter((p) =>
    p.startsWith("/blueprints/local/agents/")
  );

  const blueprintPaths = Object.keys(currentFiles).filter((p) =>
    p.startsWith("/blueprints/local/blueprints/")
  );

  const saveAgent = useCallback(
    (agent: AgentYAMLSpec, allSpecs?: AgentYAMLSpec[]) => {
      return saveAgentToSession(agent, allSpecs);
    },
    []
  );

  const saveBlueprint = useCallback(
    (
      name: string,
      description: string,
      agentSpecs: AgentYAMLSpec[],
      options?: { category?: string; tags?: string[]; visibility?: string }
    ) => {
      return saveBlueprintToSession(name, description, agentSpecs, options);
    },
    []
  );

  const getFile = useCallback((path: string) => {
    return currentFiles[path] || null;
  }, [currentFiles]);

  const clear = useCallback(() => {
    clearSession();
  }, []);

  return {
    // State
    files: currentFiles,
    agentPaths,
    blueprintPaths,
    fileCount: Object.keys(currentFiles).length,

    // Actions
    saveAgent,
    saveBlueprint,
    getFile,
    clear,
  };
}
