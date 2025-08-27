# Makefile for bootstrapping the AI Assistant in a new project

# --- Colors for better output ---
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m

.PHONY: ai-setup
ai-setup:
	@echo "${YELLOW}--- AI Assistant Project Bootstrap ---${NC}"
	@echo "This will create the necessary configuration files for the AI Assistant."
	@echo ""

	# --- Gather User Input ---
	@read -p "Enter a short project name (e.g., trading-app): " PROJECT_NAME; \
	read -p "Enter your OCI Namespace: " OCI_NAMESPACE; \
	read -p "Enter your OCI Bucket Name for RAG indexes: " OCI_BUCKET; \
	read -p "Enter your OCI Region (e.g., eu-frankfurt-1): " OCI_REGION; \
	export PROJECT_NAME OCI_NAMESPACE OCI_BUCKET OCI_REGION; \
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
	echo "# .ai_config.yml\n# Configuration for the AI Assistant in the $${PROJECT_NAME} project.\n\n\
rag:\n\
  # Enable the cloud-based workflow with branch-specific indexes.\n\
  enable_branch_awareness: true\n\
  enable_reranking: true\n\
\n\
  # Connection details for the shared OCI bucket.\n\
  oracle_cloud:\n\
    namespace: \"$${OCI_NAMESPACE}\"\n\
    bucket: \"$${OCI_BUCKET}\"\n\
    region: \"$${OCI_REGION}\"" > .ai_config.yml; \
	echo "${GREEN}Done.${NC}"; \
	\
	# --- Create .aiignore ---
	@echo "${YELLOW}--> Creating a default .aiignore file...${NC}"; \
	echo "# Exclude common files from the RAG index to keep it clean and relevant.\n\n\
.git/\n\
.venv/\n\
venv/\n\
__pycache__/\n\
*.pyc\n\
*.log\n\
\n\
# AI Assistant specific directories\n\
.ai_rag_index/\n\
.ai_sessions/\n\
ai_runs/\n\
\n\
# Project-specific ignores (add your own here)\n\
/secrets/\n\
/data/\n\
/tests/fixtures/" > .aiignore; \
	echo "${GREEN}Done.${NC}"; \
	\
	# --- Create smart-indexing.yml ---
	@echo "${YELLOW}--> Creating .github/workflows/smart-indexing.yml...${NC}"; \
	echo "# GitHub Actions workflow to automatically index the codebase for RAG.\n\
name: Smart RAG Indexing\n\
\n\
on:\n\
  push:\n\
    branches:\n\
      - main\n\
      - develop\n\
      - 'feature/**'\n\
      - 'release/**'\n\
    paths-ignore:\n\
      - 'docs/**'\n\
      - '*.md'\n\
  workflow_dispatch:\n\
\n\
concurrency:\n\
  group: indexing-\$${{ github.ref }}\n\
  cancel-in-progress: true\n\
\n\
permissions:\n\
  contents: read\n\
  issues: write\n\
\n\
env:\n\
  OCI_NAMESPACE: \$${{ vars.OCI_NAMESPACE }}\n\
  OCI_BUCKET: \$${{ vars.OCI_BUCKET }}\n\
  OCI_REGION: \$${{ vars.OCI_REGION }}\n\
  BRANCH_NAME: \$${{ github.ref_name }}\n\
\n\
jobs:\n\
  index-codebase:\n\
    runs-on: ubuntu-latest\n\
    timeout-minutes: 30\n\
    steps:\n\
      - name: Checkout Project Repository\n\
        uses: actions/checkout@v4\n\
\n\
      - name: Checkout AI Assistant Repository\n\
        uses: actions/checkout@v4\n\
        with:\n\
          repository: venoajie/my-ai-assistant\n\
          ref: develop\n\
          path: my-ai-assistant\n\
\n\
      - name: Setup Python\n\
        uses: actions/setup-python@v5\n\
        with:\n\
          python-version: '3.12'\n\
          cache: 'pip'\n\
\n\
      - name: Install AI Assistant (with indexing tools)\n\
        run: pip install -e ./my-ai-assistant[indexing]\n\
\n\
      - name: Configure OCI CLI\n\
        run: |\n\
          pip install oci-cli\n\
          mkdir -p ~/.oci\n\
          echo \"[DEFAULT]\\nuser=\${{ secrets.OCI_USER_OCID }}\\nfingerprint=\${{ secrets.OCI_FINGERPRINT }}\\ntenancy=\${{ secrets.OCI_TENANCY_OCID }}\\nregion=\${{ env.OCI_REGION }}\\nkey_file=~/.oci/api_key.pem\" > ~/.oci/config\n\
          echo \"\${{ secrets.OCI_API_KEY }}\" > ~/.oci/api_key.pem\n\
          chmod 600 ~/.oci/api_key.pem\n\
          chmod 600 ~/.oci/config\n\
          oci os ns get\n\
\n\
      - name: Run Indexer\n\
        run: ai-index . --branch \"\$${{ env.BRANCH_NAME }}\"\n\
\n\
      - name: Upload Index to Object Storage\n\
        run: |\n\
          INDEX_DIR=\".ai_rag_index\"\n\
          TIMESTAMP=\$(date +%Y%m%d_%H%M%S)\n\
          tar -czf index.tar.gz -C \"\$${INDEX_DIR}\" .\n\
          oci os object put --force --namespace \"\$${OCI_NAMESPACE}\" --bucket-name \"\$${OCI_BUCKET}\" --name \"indexes/\$${{ env.BRANCH_NAME }}/archive/\$${{TIMESTAMP}}_\$${{ github.sha }}.tar.gz\" --file index.tar.gz\n\
          oci os object put --force --namespace \"\$${OCI_NAMESPACE}\" --bucket-name \"\$${OCI_BUCKET}\" --name \"indexes/\$${{ env.BRANCH_NAME }}/latest/index.tar.gz\" --file index.tar.gz\n" > .github/workflows/smart-indexing.yml; \
	echo "${GREEN}Done.${NC}"; \
	\
	# --- Final Instructions ---
	@echo "\n\n${GREEN}✅ Bootstrap complete!${NC}"; \
	@echo "${YELLOW}--- NEXT STEPS ---${NC}"; \
	@echo "1. Add the required secrets (e.g., OCI_API_KEY) to your GitHub repository settings."; \
	@echo "2. Commit the new files (.ai_config.yml, .aiignore, .github/) to your repository."; \
	@echo "3. Push your commit to trigger the first RAG indexing run."; \
	@echo ""

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make ai-setup    - Interactively creates the configuration files for the AI Assistant."
