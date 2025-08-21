#!/usr/bin/env python3
"""
TODO: This visualization tool needs to be updated and integrated with MkDocs documentation system.

Current status:
- Basic DDD architecture visualization
- Needs integration with MkDocs
- Requires proper documentation formatting
- Should be accessible from docs/ directory

Integration plan:
1. Update to work with MkDocs
2. Add proper documentation
3. Create interactive diagrams
4. Integrate with documentation build process
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# DDD Layer Definitions
DDD_LAYERS = {
    "interface": {
        "name": "Interface Layer",
        "color": "#8dd3c7",
        "modules": ["src/mancer/interface"],
        "description": "User-facing components (CLI, API, etc.)",
    },
    "application": {
        "name": "Application Layer",
        "color": "#ffffb3",
        "modules": ["src/mancer/application"],
        "description": "Orchestration, command execution, workflow",
    },
    "domain": {
        "name": "Domain Layer",
        "color": "#bebada",
        "modules": ["src/mancer/domain"],
        "description": "Core business logic, models, interfaces",
    },
    "infrastructure": {
        "name": "Infrastructure Layer",
        "color": "#fb8072",
        "modules": ["src/mancer/infrastructure"],
        "description": "External systems, concrete implementations",
    },
}

# Subdomain mapping
DDD_SUBDOMAINS = {
    "src/mancer/domain/interface": {
        "name": "Domain Interfaces",
        "color": "#80b1d3",
        "description": "Contracts between components",
    },
    "src/mancer/domain/model": {
        "name": "Domain Models",
        "color": "#fdb462",
        "description": "Core business entities",
    },
    "src/mancer/domain/service": {
        "name": "Domain Services",
        "color": "#b3de69",
        "description": "Business operations on models",
    },
    "src/mancer/infrastructure/backend": {
        "name": "Execution Backends",
        "color": "#fccde5",
        "description": "Command execution environments",
    },
    "src/mancer/infrastructure/command": {
        "name": "Command Implementations",
        "color": "#d9d9d9",
        "description": "Concrete command implementations",
    },
    "src/mancer/infrastructure/factory": {
        "name": "Factories",
        "color": "#bc80bd",
        "description": "Object creation services",
    },
}


def install_dependencies():
    """Install required dependencies automatically."""
    dependencies = ["graphviz"]

    try:
        import pip

        # Special handling for tach
        try:
            subprocess.run(["tach", "--version"], check=True, capture_output=True)
            print("Found tach installation.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing tach...")
            subprocess.run([sys.executable, "-m", "pip", "install", "tach"], check=True)
            # Verify installation
            try:
                subprocess.run(["tach", "--version"], check=True, capture_output=True)
                print("Tach installed successfully.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    "Error: Failed to install tach. Please install it manually with 'pip install tach'."
                )
                sys.exit(1)

        # Install other dependencies
        for dep in dependencies:
            try:
                if dep == "graphviz":
                    # Check for the dot command
                    if shutil.which("dot") is None:
                        raise ImportError("Graphviz executable not found")
                    else:
                        print("Found Graphviz installation.")
            except (ImportError, ModuleNotFoundError):
                print(f"Installing {dep}...")
                if dep == "graphviz":
                    # Prompt for Graphviz installation since it's a system package
                    system = get_operating_system()
                    if system == "linux":
                        print("Graphviz needs to be installed.")
                        install = input("Install Graphviz with apt-get? (y/n): ").lower()
                        if install == "y":
                            subprocess.run(["sudo", "apt-get", "update"], check=True)
                            subprocess.run(
                                ["sudo", "apt-get", "install", "-y", "graphviz"],
                                check=True,
                            )
                        else:
                            print("Please install Graphviz manually and run the script again.")
                            sys.exit(1)
                    elif system == "macos":
                        print("Graphviz needs to be installed.")
                        install = input("Install Graphviz with brew? (y/n): ").lower()
                        if install == "y":
                            try:
                                subprocess.run(["brew", "install", "graphviz"], check=True)
                            except:
                                print("Please install Homebrew first: https://brew.sh/")
                                sys.exit(1)
                        else:
                            print("Please install Graphviz manually and run the script again.")
                            sys.exit(1)
                    else:  # Windows or other
                        print("Please install Graphviz manually:")
                        print("- Windows: https://graphviz.org/download/")
                        print("- Linux: sudo apt-get install graphviz")
                        print("- macOS: brew install graphviz")
                        sys.exit(1)
    except Exception as e:
        print(f"Error installing dependencies: {str(e)}")
        sys.exit(1)


def get_operating_system():
    """Detect the operating system."""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform.startswith("win"):
        return "windows"
    else:
        return "unknown"


def run_tach_analysis():
    """Run tach analysis and return data as JSON."""
    try:
        # Create a temporary file for the dependency map
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        # Run tach map to get dependency information
        print("Running tach map to get dependency information...")
        map_result = subprocess.run(
            ["tach", "map", "--output", temp_path],
            check=True,
            capture_output=True,
            text=True,
        )

        # Read the dependency map
        with open(temp_path, "r") as f:
            dependency_data = json.load(f)

        # Clean up the temporary file
        try:
            os.remove(temp_path)
        except:
            pass

        # Transform the data into the format expected by generate_dot_file
        transformed_data = {"modules": {}, "dependencies": []}

        # Extract modules and dependencies
        for source, targets in dependency_data.items():
            # Add the source module
            transformed_data["modules"][source] = {}

            # Add dependencies
            for target in targets:
                transformed_data["dependencies"].append(
                    {
                        "from": source,
                        "to": target,
                        "count": 1,  # We don't have count information, so default to 1
                    }
                )

        return transformed_data
    except subprocess.CalledProcessError as e:
        print(f"Error during tach analysis: {e}")
        print(f"stderr output: {e.stderr}")

        # Try alternative approach with tach show if map failed
        try:
            print("Trying alternative approach with tach show...")
            with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as temp_file:
                temp_path = temp_file.name

            show_result = subprocess.run(
                ["tach", "show", "--out", temp_path],
                check=True,
                capture_output=True,
                text=True,
            )

            # Since tach show generates a DOT file, we need to extract module info from it
            modules = {}
            dependencies = []

            with open(temp_path, "r") as f:
                dot_content = f.read()

            # Extract module names from node definitions in DOT file
            import re

            # Find module nodes
            node_pattern = re.compile(r'"([^"]+)"\s*\[')
            for match in node_pattern.finditer(dot_content):
                module_name = match.group(1)
                modules[module_name] = {}

            # Find dependencies from edges
            edge_pattern = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
            for match in edge_pattern.finditer(dot_content):
                from_module = match.group(1)
                to_module = match.group(2)
                dependencies.append({"from": from_module, "to": to_module, "count": 1})

            # Clean up
            try:
                os.remove(temp_path)
            except:
                pass

            return {"modules": modules, "dependencies": dependencies}

        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
            print("Please make sure your project structure is compatible with tach.")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error processing JSON output from tach: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during tach analysis: {e}")
        sys.exit(1)


def generate_dot_file(tach_data, output_file, detailed=False):
    """Generate DOT file from tach analysis."""
    modules = tach_data.get("modules", {})
    dependencies = tach_data.get("dependencies", [])

    # Filter modules to only include Mancer-related paths
    valid_modules = {}
    for module_path in modules:
        if "src/mancer" in module_path:
            valid_modules[module_path] = modules[module_path]

    # Filter dependencies to only include Mancer-related paths
    valid_dependencies = []
    for dep in dependencies:
        from_module = dep.get("from", "")
        to_module = dep.get("to", "")
        if "src/mancer" in from_module and "src/mancer" in to_module:
            valid_dependencies.append(dep)

    with open(output_file, "w") as f:
        # Start of DOT file
        f.write('digraph "Mancer DDD Architecture" {\n')
        f.write('  rankdir="TB";\n')
        f.write('  node [shape=box, style=filled, fontname="Arial"];\n')
        f.write('  edge [fontname="Arial", fontsize=10];\n')
        f.write("  compound=true;\n\n")

        # Define subgraphs for DDD layers
        for layer_id, layer_info in DDD_LAYERS.items():
            f.write(f'  subgraph "cluster_{layer_id}" {{\n')
            f.write(f'    label="{layer_info["name"]}";\n')
            f.write("    style=filled;\n")
            f.write(f'    color="{layer_info["color"]}";\n')
            f.write("    fontsize=16;\n")
            f.write(f'    tooltip="{layer_info["description"]}";\n')

            # If detailed diagram, add subdomains
            if detailed:
                # First, collect all modules for this layer
                layer_modules = {}
                for module_path in valid_modules:
                    if any(module_path.startswith(m) for m in layer_info["modules"]):
                        layer_modules[module_path] = valid_modules[module_path]

                # Process subdomains for this layer
                for subdomain_path, subdomain_info in DDD_SUBDOMAINS.items():
                    if any(subdomain_path.startswith(m) for m in layer_info["modules"]):
                        subdir_id = subdomain_path.replace("/", "_").replace(".", "_")
                        f.write(f'    subgraph "cluster_{subdir_id}" {{\n')
                        f.write(f'      label="{subdomain_info["name"]}";\n')
                        f.write("      style=filled;\n")
                        f.write(f'      color="{subdomain_info["color"]}";\n')
                        f.write("      fontsize=14;\n")
                        f.write(f'      tooltip="{subdomain_info["description"]}";\n')

                        # Add modules belonging to this subdomain
                        subdomain_module_added = False
                        for module_path in layer_modules:
                            if module_path.startswith(subdomain_path):
                                module_id = module_path.replace("/", "_").replace(".", "_")
                                f.write(
                                    f'      "{module_id}" [label="{os.path.basename(module_path)}", tooltip="{module_path}"];\n'
                                )
                                subdomain_module_added = True

                        # If no modules found for this subdomain, add a placeholder
                        if not subdomain_module_added:
                            placeholder_id = f"{subdir_id}_placeholder"
                            f.write(
                                f'      "{placeholder_id}" [label="{os.path.basename(subdomain_path)}", tooltip="{subdomain_path}", style="dashed,filled", fillcolor="#f5f5f5"];\n'
                            )

                        f.write("    }\n\n")

                # Add modules that don't belong to any subdomain directly to the layer
                for module_path in layer_modules:
                    if not any(module_path.startswith(s) for s in DDD_SUBDOMAINS):
                        module_id = module_path.replace("/", "_").replace(".", "_")
                        f.write(
                            f'    "{module_id}" [label="{os.path.basename(module_path)}", tooltip="{module_path}"];\n'
                        )

            # For simple diagram, just add all modules for this layer
            else:
                layer_module_added = False
                for module_path in valid_modules:
                    if any(module_path.startswith(m) for m in layer_info["modules"]):
                        module_id = module_path.replace("/", "_").replace(".", "_")
                        f.write(
                            f'    "{module_id}" [label="{os.path.basename(module_path)}", tooltip="{module_path}"];\n'
                        )
                        layer_module_added = True

                # If no modules found for this layer, add a placeholder
                if not layer_module_added:
                    placeholder_id = f"{layer_id}_placeholder"
                    f.write(
                        f'    "{placeholder_id}" [label="{layer_info["name"]}", tooltip="No modules found", style="dashed,filled", fillcolor="#f5f5f5"];\n'
                    )

            f.write("  }\n\n")

        # Add dependencies
        for dep in valid_dependencies:
            from_module = dep.get("from", "").replace("/", "_").replace(".", "_")
            to_module = dep.get("to", "").replace("/", "_").replace(".", "_")
            count = dep.get("count", 0)

            # Add edge with weight
            f.write(f'  "{from_module}" -> "{to_module}" [label="{count}", weight={count}];\n')

        # Add special edges for showing DDD pattern
        f.write("\n  # DDD pattern dependencies\n")
        interface_node = "src_mancer_interface"
        application_node = "src_mancer_application"
        domain_node = "src_mancer_domain"
        infrastructure_node = "src_mancer_infrastructure"

        # Check if nodes exist, if not use placeholders
        if not any(
            module.replace("/", "_").replace(".", "_") == interface_node for module in valid_modules
        ):
            interface_node = "interface_placeholder"
            f.write(f'  "{interface_node}" [label="Interface Layer", style="invis"];\n')

        if not any(
            module.replace("/", "_").replace(".", "_") == application_node
            for module in valid_modules
        ):
            application_node = "application_placeholder"
            f.write(f'  "{application_node}" [label="Application Layer", style="invis"];\n')

        if not any(
            module.replace("/", "_").replace(".", "_") == domain_node for module in valid_modules
        ):
            domain_node = "domain_placeholder"
            f.write(f'  "{domain_node}" [label="Domain Layer", style="invis"];\n')

        if not any(
            module.replace("/", "_").replace(".", "_") == infrastructure_node
            for module in valid_modules
        ):
            infrastructure_node = "infrastructure_placeholder"
            f.write(f'  "{infrastructure_node}" [label="Infrastructure Layer", style="invis"];\n')

        f.write(
            f'  "{interface_node}" -> "{application_node}" [color="#1f78b4", style=dashed, penwidth=2];\n'
        )
        f.write(
            f'  "{application_node}" -> "{domain_node}" [color="#1f78b4", style=dashed, penwidth=2];\n'
        )
        f.write(
            f'  "{domain_node}" -> "{infrastructure_node}" [color="#1f78b4", style=dashed, penwidth=2];\n'
        )

        # End of DOT file
        f.write("}\n")


def generate_diagram(dot_file, output_file, format="png"):
    """Generate diagram from DOT file."""
    try:
        subprocess.run(["dot", f"-T{format}", dot_file, f"-o{output_file}"], check=True)
        print(f"Diagram generated: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating diagram: {e}")
        sys.exit(1)


def generate_legend(output_dir, format="png"):
    """Generate legend explaining colors and layers."""
    legend_dot = os.path.join(output_dir, "legend.dot")
    legend_output = os.path.join(output_dir, f"legend.{format}")

    with open(legend_dot, "w") as f:
        f.write('digraph "Mancer DDD Legend" {\n')
        f.write('  node [shape=box, style=filled, fontname="Arial"];\n')
        f.write('  rankdir="TB";\n\n')

        # Title
        f.write('  label="Mancer DDD Architecture - Legend";\n')
        f.write("  fontsize=20;\n")
        f.write('  labelloc="t";\n\n')

        # Layers
        f.write("  subgraph cluster_layers {\n")
        f.write('    label="DDD Layers";\n')
        f.write('    style="rounded";\n\n')

        for i, (layer_id, layer_info) in enumerate(DDD_LAYERS.items()):
            f.write(
                f'    layer_{i} [label="{layer_info["name"]}", fillcolor="{layer_info["color"]}", tooltip="{layer_info["description"]}"];\n'
            )

        f.write("  }\n\n")

        # Subdomains
        f.write("  subgraph cluster_subdomains {\n")
        f.write('    label="Subdomains";\n')
        f.write('    style="rounded";\n\n')

        for i, (subdomain_path, subdomain_info) in enumerate(DDD_SUBDOMAINS.items()):
            f.write(
                f'    subdomain_{i} [label="{subdomain_info["name"]}", fillcolor="{subdomain_info["color"]}", tooltip="{subdomain_info["description"]}"];\n'
            )

        f.write("  }\n")
        f.write("}\n")

    generate_diagram(legend_dot, legend_output, format)


def open_diagram(diagram_path):
    """Open the generated diagram with the system's default viewer."""
    system = get_operating_system()

    try:
        if system == "linux":
            subprocess.run(["xdg-open", diagram_path], check=False)
        elif system == "macos":
            subprocess.run(["open", diagram_path], check=False)
        elif system == "windows":
            os.startfile(diagram_path)
        else:
            print("Unable to automatically open the diagram on this system.")
            print(f"Diagram is located at: {diagram_path}")
    except Exception as e:
        print(f"Error opening diagram: {str(e)}")
        print(f"Diagram is located at: {diagram_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DDD Architecture Visualization Tool for Mancer Project"
    )
    parser.add_argument("--output-dir", default="./diagrams", help="Output directory for files")
    parser.add_argument(
        "--format",
        default="png",
        choices=["dot", "png", "svg", "pdf"],
        help="Output format",
    )
    parser.add_argument("--detailed", action="store_true", help="Generate detailed diagram")
    args = parser.parse_args()

    print("==== Mancer DDD Architecture Visualizer ====")

    # Install dependencies if needed
    print("Checking and installing dependencies...")
    install_dependencies()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Create paths to output files
    dot_file = os.path.join(args.output_dir, "mancer_ddd.dot")
    diagram_output = os.path.join(args.output_dir, f"mancer_ddd.{args.format}")

    # Analyze project using tach
    print("Analyzing project with tach...")
    tach_data = run_tach_analysis()

    # Generate DOT file
    print(f"Generating DOT file: {dot_file}")
    generate_dot_file(tach_data, dot_file, args.detailed)

    # Generate diagram
    if args.format != "dot":
        print(f"Generating {args.format} diagram: {diagram_output}")
        generate_diagram(dot_file, diagram_output, args.format)

    # Generate legend
    print("Generating legend...")
    generate_legend(args.output_dir, args.format)

    print("\nVisualization completed successfully!")
    print(f"Output files have been saved to: {os.path.abspath(args.output_dir)}")

    # Ask to open diagram
    if args.format != "dot" and os.path.exists(diagram_output):
        open_choice = input("Open the generated diagram now? (y/n): ").lower()
        if open_choice == "y":
            open_diagram(diagram_output)


if __name__ == "__main__":
    main()
