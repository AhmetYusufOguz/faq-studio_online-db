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
# Copy backend application
	cp -r backend/app $(BUILD_DIR)/opt/faq-studio/
	cp backend/requirements.txt $(BUILD_DIR)/opt/faq-studio/
	
# Copy data files
	cp data/*.json $(BUILD_DIR)/var/lib/faq-studio/data/ 2>/dev/null || true
	
# Create install scripts
	echo '#!/bin/bash' > $(BUILD_DIR)/opt/faq-studio/install-ollama.sh
	echo 'curl -fsSL https://ollama.ai/install.sh | sh' >> $(BUILD_DIR)/opt/faq-studio/install-ollama.sh
	chmod +x $(BUILD_DIR)/opt/faq-studio/install-ollama.sh

# Create configuration files
.PHONY: create-configs
create-configs:
	@echo "Creating configuration files..."
# Create environment config
	cat > $(BUILD_DIR)/etc/faq-studio/config.env << EOF
# FAQ Studio Configuration
	DATABASE_URL=postgresql://user:pass@localhost:5432/faqdb
	OLLAMA_BASE_URL=http://localhost:11434
	EMBED_MODEL=bge-m3
	SIM_THRESHOLD=0.70
	JSON_PATH=/var/lib/faq-studio/data/questions.json
	CATEGORIES_PATH=/var/lib/faq-studio/data/categories.json
	CHROMA_DB_PATH=/var/lib/faq-studio/chroma_db
	HOST=0.0.0.0
	PORT=8000
	LOG_LEVEL=INFO
	DEBUG=false
	EOF

	# Create systemd service files
	cat > $(BUILD_DIR)/etc/systemd/system/ollama.service << 'EOF'
	[Unit]
	Description=Ollama AI Service
	After=network.target

	[Service]
	Type=simple
	User=ollama
	Group=ollama
	ExecStart=/usr/local/bin/ollama serve
	Environment=OLLAMA_HOST=127.0.0.1:11434
	Restart=always
	RestartSec=5

	[Install]
	WantedBy=multi-user.target
	EOF

	cat > $(BUILD_DIR)/etc/systemd/system/faq-studio.service << 'EOF'
	[Unit]
	Description=FAQ Studio API
	After=network.target ollama.service
	Requires=ollama.service

	[Service]
	Type=simple
	User=faq-studio
	Group=faq-studio
	WorkingDirectory=/opt/faq-studio
	ExecStart=/opt/faq-studio/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
	EnvironmentFile=/etc/faq-studio/config.env
	Restart=always
	RestartSec=5

	[Install]
	WantedBy=multi-user.target
	EOF

# Create debian control files
.PHONY: create-control
create-control:
	@echo "Creating debian control files..."
	
	# Create control file
	cat > $(BUILD_DIR)/DEBIAN/control << EOF
Package: $(PACKAGE_NAME)
Version: $(VERSION)
Section: utils
Priority: optional
Architecture: $(ARCH)
Depends: python3 (>= 3.8), python3-pip, python3-venv, curl, systemd
Maintainer: FAQ Studio <admin@faq-studio.local>
Description: FAQ Studio - AI-powered FAQ management system
	FAQ Studio is an AI-powered FAQ management system that uses
	Ollama for embeddings and supports PostgreSQL backend.
	.
	This package includes:
	- FastAPI web application
	- Ollama AI service integration
	- Systemd service management
	- Web-based question management interface
	EOF

	# Create postinst script
	cat > $(BUILD_DIR)/DEBIAN/postinst << 'EOF'
#!/bin/bash
	set -e

# Create users
	if ! getent group ollama > /dev/null 2>&1; then
		addgroup --system ollama
	fi

	if ! getent passwd ollama > /dev/null 2>&1; then
		adduser --system --home /var/lib/ollama --shell /bin/false --group ollama
	fi

	if ! getent group faq-studio > /dev/null 2>&1; then
		addgroup --system faq-studio
	fi

	if ! getent passwd faq-studio > /dev/null 2>&1; then
		adduser --system --home /var/lib/faq-studio --shell /bin/false --group faq-studio
	fi

# Set permissions
chown -R faq-studio:faq-studio /opt/faq-studio
chown -R faq-studio:faq-studio /var/lib/faq-studio
	chmod 755 /opt/faq-studio
	chmod -R 644 /etc/faq-studio/config.env

# Create Python virtual environment
	if [ ! -d "/opt/faq-studio/venv" ]; then
		python3 -m venv /opt/faq-studio/venv
		chown -R faq-studio:faq-studio /opt/faq-studio/venv
	fi

# Install Python dependencies
	/opt/faq-studio/venv/bin/pip install --upgrade pip
	/opt/faq-studio/venv/bin/pip install -r /opt/faq-studio/requirements.txt

# Install Ollama
	if [ ! -f "/usr/local/bin/ollama" ]; then
		echo "Installing Ollama..."
		/opt/faq-studio/install-ollama.sh
	fi

# Create Ollama directories
	mkdir -p /var/lib/ollama
	chown ollama:ollama /var/lib/ollama

# Reload systemd and enable services
	systemctl daemon-reload
	systemctl enable ollama.service
	systemctl enable faq-studio.service

# Start services
	systemctl start ollama.service
	sleep 5  # Wait for Ollama to start

# Pull the embedding model
	echo "Pulling embedding model..."
	runuser -u ollama -- /usr/local/bin/ollama pull bge-m3

# Start FAQ Studio service
	systemctl start faq-studio.service

	echo ""
	echo "FAQ Studio installation completed!"
	echo "- Ollama is running on http://localhost:11434"
	echo "- FAQ Studio is running on http://localhost:8000"
	echo ""
	echo "Configuration file: /etc/faq-studio/config.env"
	echo "Edit the DATABASE_URL in the config file to connect to your remote database."
	echo ""
	echo "To restart services:"
	echo "  sudo systemctl restart ollama.service"
	echo "  sudo systemctl restart faq-studio.service"
	echo ""
	EOF

	chmod 755 $(BUILD_DIR)/DEBIAN/postinst

	# Create prerm script (before removal)
	cat > $(BUILD_DIR)/DEBIAN/prerm << 'EOF'
#!/bin/bash
	set -e

	if [ "$$1" = "remove" ]; then
		# Stop services
		systemctl stop faq-studio.service || true
		systemctl stop ollama.service || true
		
		# Disable services
		systemctl disable faq-studio.service || true
		systemctl disable ollama.service || true
	fi
	EOF

	chmod 755 $(BUILD_DIR)/DEBIAN/prerm

	# Create postrm script (after removal)
	cat > $(BUILD_DIR)/DEBIAN/postrm << 'EOF'
#!/bin/bash
	set -e

	if [ "$$1" = "purge" ]; then
		# Remove systemd service files
		rm -f /etc/systemd/system/ollama.service
		rm -f /etc/systemd/system/faq-studio.service
		systemctl daemon-reload
		
# Remove users (optional - commented out to preserve data)
# deluser --quiet faq-studio || true
# deluser --quiet ollama || true

# Remove data directories (optional - commented out to preserve data)
# rm -rf /var/lib/faq-studio
# rm -rf /var/lib/ollama
		
		echo "FAQ Studio removed. Data directories preserved."
		echo "To completely remove data:"
		echo "  sudo rm -rf /var/lib/faq-studio"
		echo "  sudo rm -rf /var/lib/ollama"
	fi
	EOF

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
	@echo "  create-aiven-db - Show instructions for Aiven database setup"
	@echo "  help           - Show this help"