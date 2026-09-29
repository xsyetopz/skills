# Architecture Overview

{Two to four sentences: what the system does, for whom, and its shape
(one process, services, a library). Durable facts only.}

## 1. Project Structure

```text
{repo}/                    # repository root
├── {dir}/                 # {one responsibility}
│   └── {file}             # {role}
└── {dir}/                 # {one responsibility}
```

## 2. High-Level System Diagram

```mermaid
flowchart LR
    {Actor} --> {Component}
    {Component} --> {Store}[({Store})]
```

## 3. Core Components

### 3.1. {Component}

`{path}`. {Responsibility, main inputs and outputs, what it calls, the
state it owns.}

## 4. Data Stores

### 4.1. {Store}

{Technology, what it holds, main tables, who writes it, how the schema
changes. Or: None: all state is in memory.}

## 5. External Integrations / APIs

{Service, call site, integration method. Or: None.}

## 6. Deployment & Infrastructure

{Artifacts, configuration, CI, hosting, each with its file. Or: Not
evident from the repository.}

## 7. Security Considerations

- {Control and the code that enforces it, or a missing control.}

## 8. Development & Testing Environment

{Runtime and tool versions the project requires.}

```sh
{command that was run and passed}
```

### Invariants

- {Rule the code keeps, often an absence, with its check command above.}

## 9. Future Considerations / Roadmap

{Documented plans with their source. Then, labeled:}

Recommendations, not documented plans:

- {Recommendation.}

## 10. Project Identification

- Project name: {name}
- Repository URL: {url, or Not evident from the repository.}
- Primary contact: {owner, or Not evident from the repository.}
- Date of last update: {YYYY-MM-DD}

## 11. Glossary / Acronyms

- {Term}: {project-specific meaning.}
