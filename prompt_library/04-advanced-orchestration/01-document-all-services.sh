#!/bin/bash
set -e

# ---
# WORKFLOW 4: ADVANCED ORCHESTRATION
#
# GOAL:
# To demonstrate how to use a shell script as a "conductor" to orchestrate
# multiple, focused calls to the AI "specialist". This is the canonical
# pattern for safely processing many files.
# ---

# --- Configuration ---

# The specialist for this task.
# 'dca-1' is the Documentation & Content Architect.
specialist_persona="domains/programming/dca-1"

# An array of service directories we want to process.
services_to_document=("services/service-alpha" "services/service-beta")

# --- Execution ---
echo "🚀 Starting batch documentation workflow..."

# Loop through each service directory.
for service_dir in "${services_to_document[@]}"; do
    
    # Check if the directory and a README exist.
    if [ -d "$service_dir" ] && [ ! -f "$service_dir/README.md" ]; then
        echo "---"
        echo "Processing service: $service_dir"
        
        # Dynamically find the main source file for context.
        main_file=$(find "$service_dir" -name "main.py")
        
        if [ -z "$main_file" ]; then
            echo "   - WARNING: No main.py found in $service_dir. Skipping."
            continue
        fi

        # Define the query for this specific iteration.
        query="<ACTION>Create a simple README.md file for the service in the attached file '$main_file'. The README should describe the service's purpose based on its source code.</ACTION>"
        
        # Use the safe, two-stage workflow for each service.
        output_dir="ai_runs/doc_$(basename "$service_dir")_$(date +%s)"
        
        # STAGE 1: Generate the plan for this single service.
        echo "   - [1/2] Generating README plan..."
        ai --persona "$specialist_persona" \
           --output-dir "$output_dir" \
           -f "$main_file" \
           "$query"
           
        # STAGE 2: Execute the plan for this single service.
        echo "   - [2/2] Applying README changes..."
        ai-execute "$output_dir" --confirm
        
        echo "   - ✅ Successfully created README for $service_dir"
    else
        echo "---"
        echo "Skipping service (already has a README or does not exist): $service_dir"
    fi
done

echo "---"
echo "🎉 Batch documentation workflow complete."