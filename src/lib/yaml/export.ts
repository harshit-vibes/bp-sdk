/**
 * YAML Export Module
 *
 * Exports blueprint and agent configurations to YAML format.
 * Generates a downloadable ZIP file containing all YAML files.
 *
 * YAML Schema (aligned with bp-sdk):
 * - Agent YAML: name, description, model, temperature, role, goal, instructions,
 *               features, usage_description (workers), sub_agents (managers)
 * - Blueprint YAML: name, description, category, tags, visibility, root_agents
 */

import yaml from "js-yaml";
import JSZip from "jszip";
import type { AgentYAMLSpec } from "@/lib/types";

/**
 * Consistent slugify function for filenames
 * Used across export and session storage for consistency
 */
export function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

/**
 * Get canonical filename for an agent
 * Ensures consistent naming across all YAML operations
 */
export function getAgentFilename(spec: AgentYAMLSpec): string {
  return spec.filename || `${slugify(spec.name)}.yaml`;
}

/**
 * Agent YAML structure for export
 * Includes metadata fields for proper blueprint reconstruction
 */
interface AgentYAMLExport {
  name: string;
  description: string;
  model: string;
  temperature: number;
  role: string;
  goal: string;
  instructions: string;
  features: string[];
  // Optional fields
  usage_description?: string;  // For workers: when to delegate to this agent
  sub_agents?: string[];       // For managers: worker agent filenames
}

/**
 * Blueprint YAML structure for export
 */
interface BlueprintYAMLExport {
  name: string;
  description: string;
  category: string;
  tags: string[];
  visibility: string;
  root_agents: string[];  // All agent filenames (manager first, then workers)
}

/**
 * Convert AgentYAMLSpec to exportable format
 * Includes sub_agents for managers to enable proper blueprint reconstruction
 */
function specToExport(spec: AgentYAMLSpec, allSpecs?: AgentYAMLSpec[]): AgentYAMLExport {
  const exported: AgentYAMLExport = {
    name: spec.name,
    description: spec.description,
    model: spec.model,
    temperature: spec.temperature,
    role: spec.role,
    goal: spec.goal,
    instructions: spec.instructions,
    features: spec.features || [],
  };

  // Include usage_description for workers
  if (spec.usage_description) {
    exported.usage_description = spec.usage_description;
  }

  // Include sub_agents for managers (list of worker filenames)
  if (spec.is_manager && allSpecs) {
    const workerFilenames = allSpecs
      .filter((s) => !s.is_manager)
      .map((s) => getAgentFilename(s));
    if (workerFilenames.length > 0) {
      exported.sub_agents = workerFilenames;
    }
  } else if (spec.sub_agents && spec.sub_agents.length > 0) {
    // Use existing sub_agents if provided
    exported.sub_agents = spec.sub_agents;
  }

  return exported;
}

/**
 * Generate agent YAML content
 *
 * @param spec - Agent specification
 * @param allSpecs - Optional: all agent specs (for computing sub_agents on managers)
 */
export function generateAgentYAML(
  spec: AgentYAMLSpec,
  allSpecs?: AgentYAMLSpec[]
): string {
  const exportData = specToExport(spec, allSpecs);

  // Use block scalar style for long strings
  const yamlOptions: yaml.DumpOptions = {
    lineWidth: 120,
    noRefs: true,
    sortKeys: false,
    quotingType: '"',
    forceQuotes: false,
  };

  // Build formatted object with proper field ordering
  const formatted: Record<string, unknown> = {
    name: exportData.name,
    description: exportData.description,
    model: exportData.model,
    temperature: exportData.temperature,
    role: exportData.role,
    goal: exportData.goal,
    instructions: exportData.instructions,
    features: exportData.features,
  };

  // Add optional fields in proper order
  if (exportData.usage_description) {
    formatted.usage_description = exportData.usage_description;
  }

  if (exportData.sub_agents && exportData.sub_agents.length > 0) {
    formatted.sub_agents = exportData.sub_agents;
  }

  return yaml.dump(formatted, yamlOptions);
}

/**
 * Generate blueprint YAML content
 *
 * root_agents includes all agent filenames:
 * - Manager agent first (entry point)
 * - Worker agents in order
 */
export function generateBlueprintYAML(
  name: string,
  description: string,
  agentSpecs: AgentYAMLSpec[],
  options?: {
    category?: string;
    tags?: string[];
    visibility?: string;
  }
): string {
  // Find manager and workers
  const managerSpec = agentSpecs.find((s) => s.is_manager);
  const workerSpecs = agentSpecs.filter((s) => !s.is_manager);

  // Build root_agents array: manager first, then workers
  const rootAgents: string[] = [];

  if (managerSpec) {
    rootAgents.push(getAgentFilename(managerSpec));
  }

  // Add worker filenames in order
  for (const worker of workerSpecs) {
    rootAgents.push(getAgentFilename(worker));
  }

  // Fallback if no agents
  if (rootAgents.length === 0) {
    rootAgents.push("manager.yaml");
  }

  const blueprint: BlueprintYAMLExport = {
    name,
    description: description || managerSpec?.description || `Blueprint for ${name}`,
    category: options?.category || "general",
    tags: options?.tags || [],
    visibility: options?.visibility || "private",
    root_agents: rootAgents,
  };

  return yaml.dump(blueprint, {
    lineWidth: 120,
    noRefs: true,
    sortKeys: false,
  });
}

/**
 * Generate README content
 */
function generateReadme(
  blueprintName: string,
  agentSpecs: AgentYAMLSpec[]
): string {
  const manager = agentSpecs.find((s) => s.is_manager);
  const workers = agentSpecs.filter((s) => !s.is_manager);

  let readme = `# ${blueprintName}\n\n`;

  if (manager) {
    readme += `${manager.description}\n\n`;
    readme += `## Agents\n\n`;
    readme += `### Manager: ${manager.name}\n\n`;
    readme += `${manager.role}\n\n`;
    readme += `**Goal:** ${manager.goal}\n\n`;
  }

  if (workers.length > 0) {
    readme += `### Workers\n\n`;
    for (const worker of workers) {
      readme += `#### ${worker.name}\n\n`;
      readme += `${worker.description}\n\n`;
      if (worker.usage_description) {
        readme += `**When to use:** ${worker.usage_description}\n\n`;
      }
    }
  }

  readme += `## Configuration\n\n`;
  readme += `- **Model:** ${manager?.model || "gpt-4o-mini"}\n`;
  readme += `- **Temperature:** ${manager?.temperature || 0.7}\n\n`;

  readme += `## Usage\n\n`;
  readme += "```bash\n";
  readme += `bp create ${slugify(blueprintName)}/blueprint.yaml\n`;
  readme += "```\n\n";

  readme += `---\n\n`;
  readme += `Generated by Blueprint Builder\n`;

  return readme;
}

/**
 * Export blueprint and agents to a downloadable ZIP file
 */
export async function exportToZip(
  blueprintName: string,
  agentSpecs: AgentYAMLSpec[],
  options?: {
    category?: string;
    tags?: string[];
    visibility?: string;
    includeReadme?: boolean;
  }
): Promise<Blob> {
  const zip = new JSZip();

  // Create folder structure
  const folderName = blueprintName.toLowerCase().replace(/\s+/g, "-");
  const folder = zip.folder(folderName);

  if (!folder) {
    throw new Error("Failed to create ZIP folder");
  }

  // Create agents subfolder
  const agentsFolder = folder.folder("agents");
  if (!agentsFolder) {
    throw new Error("Failed to create agents folder");
  }

  // Generate and add agent YAML files
  // Pass allSpecs for proper sub_agents computation on manager
  for (const spec of agentSpecs) {
    const yamlContent = generateAgentYAML(spec, agentSpecs);
    const filename = getAgentFilename(spec);  // Use consistent filename helper
    agentsFolder.file(filename, yamlContent);
  }

  // Generate and add blueprint.yaml
  const managerSpec = agentSpecs.find((s) => s.is_manager);
  const blueprintYaml = generateBlueprintYAML(
    blueprintName,
    managerSpec?.description || "",
    agentSpecs,
    options
  );
  folder.file("blueprint.yaml", blueprintYaml);

  // Generate and add README if requested
  if (options?.includeReadme !== false) {
    const readme = generateReadme(blueprintName, agentSpecs);
    folder.file("README.md", readme);
  }

  // Generate ZIP blob
  return zip.generateAsync({ type: "blob" });
}

/**
 * Download a ZIP blob as a file
 */
export function downloadZip(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export and download blueprint as ZIP
 *
 * Main entry point for YAML export functionality.
 *
 * @example
 * ```tsx
 * const handleExport = async () => {
 *   await exportAndDownload("My Blueprint", agentSpecs);
 * };
 * ```
 */
export async function exportAndDownload(
  blueprintName: string,
  agentSpecs: AgentYAMLSpec[],
  options?: {
    category?: string;
    tags?: string[];
    visibility?: string;
    includeReadme?: boolean;
  }
): Promise<void> {
  const blob = await exportToZip(blueprintName, agentSpecs, options);
  const filename = `${blueprintName.toLowerCase().replace(/\s+/g, "-")}.zip`;
  downloadZip(blob, filename);
}
