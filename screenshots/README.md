# IBM Bob Telemetry & Submission Screenshots

This directory contains verified full-window VS Code screenshots of active IBM Bob 2.0 sessions during the development of **VECTIS** for the IBM Bob 2.0 Hackathon on lablab.ai.

## Required Telemetry Artifacts

### 1. Plan Mode Session
- **File**: `bob-plan-mode.png`
- **Description**: Architecture, blast radius mapping, and mitigation plan generation for PR #482 session refactoring.
- **Components Active**: IBM Bob Plan Mode, AST Dependency Matrix, Context Anchor.

### 2. Task Execution & File Modification
- **Files**: `bob-task-execution.png` (also preserved as `bob-fastmcp-tools.png` and `bob-docling-extraction.png`)
- **Description**: Sesi saat Bob membaca file monorepo, mengeksekusi FastMCP tools, mengidentifikasi downstream blast radius, dan mengoptimalkan runtime server dependencies.
- **Components Active**: IBM Bob Agent Mode, FastMCP `analyze_blast_radius` tool, IBM Docling parser for PCI-DSS v4.0.1 compliance.

### 3. Granite Shim Synthesis
- **Files**: `bob-granite-shim.png` (also preserved as `bob-granite-code.png`)
- **Description**: Live autonomous backward-compatibility shim synthesis (`auth_adapter.ts`) using IBM Granite 3.0 Code with 4 ES6 Proxy traps to protect Stripe checkout and Kafka workers.
- **Components Active**: IBM Bob Agent Mode + IBM Granite 3.0 Code model.

### 4. Session Summary & Completed Tasks
- **File**: `bob-session-summary.png`
- **Description**: Ringkasan tugas dan status eksekusi akhir sesi yang membuktikan seluruh intervensi kode Bob terselesaikan dengan sukses di dalam workspace `d:\vectis`.
