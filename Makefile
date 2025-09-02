# FAQ Studio Makefile

# Variables
PACKAGE_NAME = faq-studio
VERSION = 1.0.0
ARCH = amd64
DEB_FILE = $(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb
BUILD_DIR = debian

# Default target
.PHONY: all
all: clean build

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -f *.deb
	rm -f *.buildinfo
	rm -f *.changes

# Create directory structure
.PHONY: prepare
prepare:
	@echo "Creating directory structure..."
	mkdir -p $(BUILD_DIR)/DEBIAN
	mkdir -p $(BUILD_DIR)/etc/faq-studio
	mkdir -p $(BUILD_DIR)/etc/systemd/system
	mkdir -p $(BUILD_DIR)/opt/faq-studio
	mkdir -p $(BUILD_DIR)/var/lib/faq-studio/data
	mkdir -p $(BUILD_DIR)/usr/local/bin

# Copy application files
.PHONY: copy-files
copy-files: prepare
	@echo "Copying application files..."
	# Copy application (not in backend/ subdirectory)
	cp -r app $(BUILD_DIR)/opt/faq-studio/
	cp requirements.txt $(BUILD_DIR)/opt/faq-studio/ 2>/dev/null || echo "requirements.txt not found, skipping..."
	# Copy data files
	cp data/*.json $(BUILD_DIR)/var/lib/faq-studio/data/ 2>/dev/null || echo "No JSON files found in data/, skipping..."
	# Create install scripts
	echo '#!/bin/bash' > $(BUILD_DIR)/opt/faq-studio/install-ollama.sh
	echo 'curl -fsSL https://ollama.ai/install.sh | sh' >> $(BUILD_DIR)/opt/faq-studio/install-ollama.sh
	chmod +x $(BUILD_DIR)/opt/faq-studio/install-ollama.sh

# Create configuration files
.PHONY: create-configs
create-configs:
	@echo "Creating configuration files..."
	# Create environment config
	@echo "# FAQ Studio Configuration" > $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "DATABASE_URL=postgresql://user:pass@localhost:5432/faqdb" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "OLLAMA_BASE_URL=http://localhost:11434" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "EMBED_MODEL=bge-m3" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "SIM_THRESHOLD=0.70" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "JSON_PATH=/var/lib/faq-studio/data/questions.json" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "CATEGORIES_PATH=/var/lib/faq-studio/data/categories.json" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "CHROMA_DB_PATH=/var/lib/faq-studio/chroma_db" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "HOST=0.0.0.0" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "PORT=8000" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "LOG_LEVEL=INFO" >> $(BUILD_DIR)/etc/faq-studio/config.env
	@echo "DEBUG=false" >> $(BUILD_DIR)/etc/faq-studio/config.env
	# Create systemd service files
	@echo "[Unit]" > $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "Description=Ollama AI Service" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "After=network.target" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "[Service]" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "Type=simple" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "User=ollama" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "Group=ollama" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "ExecStart=/usr/local/bin/ollama serve" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "Environment=OLLAMA_HOST=127.0.0.1:11434" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "Restart=always" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "RestartSec=5" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "[Install]" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	@echo "WantedBy=multi-user.target" >> $(BUILD_DIR)/etc/systemd/system/ollama.service
	# Create FAQ Studio service
	@echo "[Unit]" > $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "Description=FAQ Studio API" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "After=network.target ollama.service" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "Requires=ollama.service" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "[Service]" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "Type=simple" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "User=faq-studio" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "Group=faq-studio" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "WorkingDirectory=/opt/faq-studio" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "ExecStart=/opt/faq-studio/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "EnvironmentFile=/etc/faq-studio/config.env" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "Restart=always" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "RestartSec=5" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "[Install]" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service
	@echo "WantedBy=multi-user.target" >> $(BUILD_DIR)/etc/systemd/system/faq-studio.service

# Create debian control files
.PHONY: create-control
create-control:
	@echo "Creating debian control files..."
	# Create control file
	@echo "Package: $(PACKAGE_NAME)" > $(BUILD_DIR)/DEBIAN/control
	@echo "Version: $(VERSION)" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Section: utils" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Priority: optional" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Architecture: $(ARCH)" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Depends: python3 (>= 3.8), python3-pip, python3-venv, curl, systemd" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Maintainer: FAQ Studio <admin@faq-studio.local>" >> $(BUILD_DIR)/DEBIAN/control
	@echo "Description: FAQ Studio - AI-powered FAQ management system" >> $(BUILD_DIR)/DEBIAN/control
	@echo " FAQ Studio is an AI-powered FAQ management system that uses" >> $(BUILD_DIR)/DEBIAN/control
	@echo " Ollama for embeddings and supports PostgreSQL backend." >> $(BUILD_DIR)/DEBIAN/control
	@echo " ." >> $(BUILD_DIR)/DEBIAN/control
	@echo " This package includes:" >> $(BUILD_DIR)/DEBIAN/control
	@echo " - FastAPI web application" >> $(BUILD_DIR)/DEBIAN/control
	@echo " - Ollama AI service integration" >> $(BUILD_DIR)/DEBIAN/control
	@echo " - Systemd service management" >> $(BUILD_DIR)/DEBIAN/control
	@echo " - Web-based question management interface" >> $(BUILD_DIR)/DEBIAN/control
	# Create postinst script
	@echo "#!/bin/bash" > $(BUILD_DIR)/DEBIAN/postinst
	@echo "set -e" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Create users" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if ! getent group ollama > /dev/null 2>&1; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    addgroup --system ollama" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if ! getent passwd ollama > /dev/null 2>&1; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    adduser --system --home /var/lib/ollama --shell /bin/false --group ollama" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if ! getent group faq-studio > /dev/null 2>&1; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    addgroup --system faq-studio" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if ! getent passwd faq-studio > /dev/null 2>&1; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    adduser --system --home /var/lib/faq-studio --shell /bin/false --group faq-studio" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Set permissions" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "chown -R faq-studio:faq-studio /opt/faq-studio" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "chown -R faq-studio:faq-studio /var/lib/faq-studio" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "chmod 755 /opt/faq-studio" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "chmod -R 644 /etc/faq-studio/config.env" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Create Python virtual environment" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if [ ! -d \"/opt/faq-studio/venv\" ]; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    python3 -m venv /opt/faq-studio/venv" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    chown -R faq-studio:faq-studio /opt/faq-studio/venv" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Install Python dependencies" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "/opt/faq-studio/venv/bin/pip install --upgrade pip" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "/opt/faq-studio/venv/bin/pip install -r /opt/faq-studio/requirements.txt" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Install Ollama" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "if [ ! -f \"/usr/local/bin/ollama\" ]; then" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    echo \"Installing Ollama...\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "    /opt/faq-studio/install-ollama.sh" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Create Ollama directories" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "mkdir -p /var/lib/ollama" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "chown ollama:ollama /var/lib/ollama" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Reload systemd and enable services" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "systemctl daemon-reload" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "systemctl enable ollama.service" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "systemctl enable faq-studio.service" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Start services" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "systemctl start ollama.service" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "sleep 5  # Wait for Ollama to start" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Pull the embedding model" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"Pulling embedding model...\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "runuser -u ollama -- /usr/local/bin/ollama pull bge-m3" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "# Start FAQ Studio service" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "systemctl start faq-studio.service" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"FAQ Studio installation completed!\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"- Ollama is running on http://localhost:11434\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"- FAQ Studio is running on http://localhost:8000\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"Configuration file: /etc/faq-studio/config.env\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"Edit the DATABASE_URL in the config file to connect to your remote database.\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"To restart services:\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"  sudo systemctl restart ollama.service\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"  sudo systemctl restart faq-studio.service\"" >> $(BUILD_DIR)/DEBIAN/postinst
	@echo "echo \"\"" >> $(BUILD_DIR)/DEBIAN/postinst
	chmod 755 $(BUILD_DIR)/DEBIAN/postinst
	# Create prerm script (before removal)
	@echo "#!/bin/bash" > $(BUILD_DIR)/DEBIAN/prerm
	@echo "set -e" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "if [ \"\$$1\" = \"remove\" ]; then" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    # Stop services" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    systemctl stop faq-studio.service || true" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    systemctl stop ollama.service || true" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    " >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    # Disable services" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    systemctl disable faq-studio.service || true" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "    systemctl disable ollama.service || true" >> $(BUILD_DIR)/DEBIAN/prerm
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/prerm
	chmod 755 $(BUILD_DIR)/DEBIAN/prerm
	# Create postrm script (after removal)
	@echo "#!/bin/bash" > $(BUILD_DIR)/DEBIAN/postrm
	@echo "set -e" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "if [ \"\$$1\" = \"purge\" ]; then" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # Remove systemd service files" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    rm -f /etc/systemd/system/ollama.service" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    rm -f /etc/systemd/system/faq-studio.service" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    systemctl daemon-reload" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    " >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # Remove users (optional - commented out to preserve data)" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # deluser --quiet faq-studio || true" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # deluser --quiet ollama || true" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # Remove data directories (optional - commented out to preserve data)" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # rm -rf /var/lib/faq-studio" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    # rm -rf /var/lib/ollama" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    " >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    echo \"FAQ Studio removed. Data directories preserved.\"" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    echo \"To completely remove data:\"" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    echo \"  sudo rm -rf /var/lib/faq-studio\"" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "    echo \"  sudo rm -rf /var/lib/ollama\"" >> $(BUILD_DIR)/DEBIAN/postrm
	@echo "fi" >> $(BUILD_DIR)/DEBIAN/postrm
	chmod 755 $(BUILD_DIR)/DEBIAN/postrm

# Build the package
.PHONY: build
build: copy-files create-configs create-control
	@echo "Building debian package..."
	dpkg-deb --build $(BUILD_DIR) $(DEB_FILE)
	@echo "Package built: $(DEB_FILE)"

# Install the package (requires sudo)
.PHONY: install
install: build
	@echo "Installing package..."
	sudo dpkg -i $(DEB_FILE)

# Uninstall the package (requires sudo)
.PHONY: uninstall
uninstall:
	@echo "Uninstalling package..."
	sudo dpkg -r $(PACKAGE_NAME)

# Purge the package and config files (requires sudo)
.PHONY: purge
purge:
	@echo "Purging package..."
	sudo dpkg --purge $(PACKAGE_NAME)

# Show package info
.PHONY: info
info:
	@echo "Package Information:"
	@echo "Name: $(PACKAGE_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Architecture: $(ARCH)"
	@echo "DEB file: $(DEB_FILE)"

# Check project structure
.PHONY: check-structure
check-structure:
	@echo "Checking project structure..."
	@echo "Current directory:"
	@pwd
	@echo ""
	@echo "Project files:"
	@ls -la
	@echo ""
	@echo "Looking for app directory:"
	@ls -la app/ 2>/dev/null || echo "app/ directory not found"
	@echo ""
	@echo "Looking for requirements.txt:"
	@ls -la requirements.txt 2>/dev/null || echo "requirements.txt not found"
	@echo ""
	@echo "Looking for data directory:"
	@ls -la data/ 2>/dev/null || echo "data/ directory not found"

# Create Aiven PostgreSQL database (helper command)
.PHONY: create-aiven-db
create-aiven-db:
	@echo "To create a free Aiven PostgreSQL database:"
	@echo "1. Go to https://aiven.io/"
	@echo "2. Sign up for a free account"
	@echo "3. Create a new PostgreSQL service"
	@echo "4. Select the free plan"
	@echo "5. Copy the connection string"
	@echo "6. Edit /etc/faq-studio/config.env"
	@echo "7. Set DATABASE_URL to your Aiven connection string"
	@echo "8. Restart the service: sudo systemctl restart faq-studio.service"

# Test installation
.PHONY: test
test:
	@echo "Testing installation..."
	@echo "Checking services status:"
	systemctl status ollama.service --no-pager || true
	systemctl status faq-studio.service --no-pager || true
	@echo ""
	@echo "Testing endpoints:"
	curl -s http://localhost:11434/api/version || echo "Ollama not responding"
	curl -s http://localhost:8000/health || echo "FAQ Studio not responding"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build          - Build the DEB package"
	@echo "  install        - Install the package (requires sudo)"
	@echo "  uninstall      - Uninstall the package (requires sudo)"
	@echo "  purge          - Purge package and configs (requires sudo)"
	@echo "  clean          - Clean build artifacts"
	@echo "  test           - Test the installation"
	@echo "  info           - Show package information"
	@echo "  check-structure - Check project structure"
	@echo "  create-aiven-db - Show instructions for Aiven database setup"
	@echo "  help           - Show this help"