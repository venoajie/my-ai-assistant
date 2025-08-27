
# Makefile for bootstrapping and managing the AI Assistant in a new project

# --- Colors for better output ---
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make ai-setup    - Interactively creates all necessary configuration files for the AI Assistant."

.PHONY: ai-setup
ai-setup:
	@echo "${YELLOW}--- AI Assistant Project Bootstrap ---${NC}"
	@echo "This will create the necessary configuration files for the AI Assistant."
	@echo "Press Enter to accept the default values in [brackets]."
	@echo ""

	# --- Gather User Input with Defaults ---
	@read -p "Enter a short project name (e.g., trading-app): " PROJECT_NAME; \
	read -p "Enter your OCI Namespace: " OCI_NAMESPACE; \
	read -p "Enter your OCI Bucket Name for RAG indexes: " OCI_BUCKET; \
	read -p "Enter your OCI Region [eu-frankfurt-1]: " OCI_REGION; \
	read -p "Enter the AI Assistant GitHub repository [venoajie/my-ai-assistant]: " AI_ASSISTANT_REPO; \
	read -p "Enter the AI Assistant branch to use [develop]: " AI_ASSISTANT_BRANCH; \
	\
	# --- Assign Defaults if input is empty ---
	: "$${OCI_REGION:=eu-frankfurt-1}"
	: "$${AI_ASSISTANT_REPO:=venoajie/my-ai-assistant}"
	: "$${AI_ASSISTANT_BRANCH:=develop}"
	export PROJECT_NAME OCI_NAMESPACE OCI_BUCKET OCI_REGION AI_ASSISTANT_REPO AI_ASSISTANT_BRANCH; \
	\
	# --- Create Directory Structure ---
	@echo "\n${YELLOW}--> Creating directory structure...${NC}"; \
	mkdir -p .ai/personas/domains/$${PROJECT_NAME}; \
	mkdir -p .ai/plugins; \
	mkdir -p .github/workflows; \
	echo "${GREEN}Done.${NC}"; \
	\
	# --- Create .ai_config.yml ---
	@echo "${YELLOW}--> Creating .ai_config.yml...${NC}"; \
	cat <<EOF > .ai_config.yml
# .ai_config.yml
# Configuration for the AI Assistant in the $${PROJECT_NAME} project.

rag:
  # Enable the cloud-based workflow with branch-specific indexes.
  enable_branch_awareness: true
  enable_reranking: true

  # Connection details for the shared OCI bucket.
  oracle_cloud:
    namespace: "$${OCI_NAMESPACE}"
    bucket: "$${OCI_BUCKET}"
    region: "$${OCI_REGION}"
EOF
	@echo "${GREEN}Done.${NC}"; \
	\
	# --- Create .aiignore ---
	@echo "${YELLOW}--> Creating a default .aiignore file...${NC}"; \
	cat <<EOF > .aiignore
# Exclude common files from the RAG index to keep it clean and relevant.
.git/
.venv/
__pycache__/
*.pyc
*.log

# AI Assistant specific directories
.ai_rag_index/
.ai_sessions/
ai_runs/

# Project-specific ignores (add your own here)
/secrets/
/data/
/tests/fixtures/
EOF
	@echo "${GREEN}Done.${NC}"; \
	\
	# --- Create smart-indexing.yml ---
	@echo "${YELLOW}--> Creating .github/workflows/smart-indexing.yml...${NC}"; \
	cat <<'EOF' > .github/workflows/smart-indexing.yml
# GitHub Actions workflow to automatically index the codebase for RAG.
name: Smart RAG Indexing

on:
  push:
    branches: [main, develop, 'feature/**', 'release/**']
    paths-ignore: ['docs/**', '*.md']
  workflow_dispatch:
    inputs:
      force_reindex:
        description: 'Force complete reindexing'
        type: boolean
        default: false

concurrency:
  group: indexing-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  issues: write

env:
  OCI_NAMESPACE: ${{ vars.OCI_NAMESPACE }}
  OCI_BUCKET: ${{ vars.OCI_BUCKET }}
  OCI_REGION: ${{ vars.OCI_REGION }}
  BRANCH_NAME: ${{ github.ref_name }}

jobs:
  index-codebase:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout Project Repository
        uses: actions/checkout@v4

      - name: Checkout AI Assistant Repository
        uses: actions/checkout@v4
        with:
          repository: $${AI_ASSISTANT_REPO}
          ref: $${AI_ASSISTANT_BRANCH}
          path: my-ai-assistant

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install All Dependencies
        run: |
          pip install -e ./my-ai-assistant[indexing]
          pip install oci-cli

      - name: Configure Oracle Cloud CLI
        env:
          OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING: true
        run: |
          mkdir -p ~/.oci
          cat > ~/.oci/config << EOC
          [DEFAULT]
          user=${{ secrets.OCI_USER_OCID }}
          fingerprint=${{ secrets.OCI_FINGERPRINT }}
          tenancy=${{ secrets.OCI_TENANCY_OCID }}
          region=${{ env.OCI_REGION }}
          key_file=~/.oci/api_key.pem
EOC
          echo "${{ secrets.OCI_API_KEY }}" > ~/.oci/api_key.pem
          chmod 600 ~/.oci/api_key.pem
          chmod 600 ~/.oci/config
          oci os ns get

      - name: Download Previous Index (for incremental update)
        id: download_previous
        run: |
          INDEX_DIR=".ai_rag_index"
          echo "Attempting to download previous index..."
          oci os object get --namespace "$${OCI_NAMESPACE}" --bucket-name "$${OCI_BUCKET}" --name "indexes/$${BRANCH_NAME}/latest/index.tar.gz" --file index.tar.gz || true
          if [ -f "index.tar.gz" ]; then
            echo "Previous index found. Unpacking for incremental update."
            mkdir -p "$${INDEX_DIR}"
            tar -xzf index.tar.gz -C "$${INDEX_DIR}"
          else
            echo "No previous index found. A full re-index will be performed."
          fi

      - name: Determine Indexing Mode
        id: mode
        run: echo "mode=${{ github.event.inputs.force_reindex == 'true' && 'full' || 'delta' }}" >> $GITHUB_OUTPUT

      - name: Run Indexer
        run: |
          ai-index . \
            --branch "$${{ env.BRANCH_NAME }}" \
            ${{ steps.mode.outputs.mode == 'full' && '--force-reindex' || '' }}

      - name: Upload Index to Object Storage
        run: |
          INDEX_DIR=".ai_rag_index"
          TIMESTAMP=$(date +%Y%m%d_%H%M%S)
          tar -czf index.tar.gz -C "$${INDEX_DIR}" .
          oci os object put --force --namespace "$${OCI_NAMESPACE}" --bucket-name "$${OCI_BUCKET}" --name "indexes/$${{ env.BRANCH_NAME }}/archive/$${TIMESTAMP}_\$${{ github.sha }}.tar.gz" --file index.tar.gz
          oci os object put --force --namespace "$${OCI_NAMESPACE}" --bucket-name "$${OCI_BUCKET}" --name "indexes/$${{ env.BRANCH_NAME }}/latest/index.tar.gz" --file index.tar.gz
EOF
	@echo "${GREEN}Done.${NC}"; \
	\
	# --- Final Instructions ---
	@echo "\n\n${GREEN}✅ Bootstrap complete!${NC}"; \
	@echo "${YELLOW}--- NEXT STEPS ---${NC}"; \
	@echo "1. Add the required secrets (OCI_USER_OCID, etc.) to your GitHub repository settings."; \
	@echo "2. Commit the new files (.ai_config.yml, .aiignore, .github/) to your repository."; \
	@echo "3. Push your commit to trigger the first RAG indexing run."; \
	@echo ""