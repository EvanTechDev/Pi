#!/bin/bash

# Script: download_pi_files.sh
# Purpose: Download output.txt and state.pkl from GitHub releases using wget

# Define URLs and target directory
URL1="https://github.com/EvanTechDev/Pi/releases/download/latest/output.txt"
URL2="https://github.com/EvanTechDev/Pi/releases/download/latest/state.pkl"
DOWNLOAD_DIR="./"

# Function to check and install wget if not present
ensure_wget() {
    if command -v wget &> /dev/null; then
        echo "[OK] wget is already installed."
        return 0
    fi

    echo "[WARN] wget not found. Attempting to install..."
    
    # Detect OS and use appropriate package manager
    if command -v apt &> /dev/null; then
        echo "[INFO] Detected Debian/Ubuntu. Using apt..."
        sudo apt update && sudo apt install -y wget
    elif command -v yum &> /dev/null; then
        echo "[INFO] Detected RHEL/CentOS. Using yum..."
        sudo yum install -y wget
    elif command -v dnf &> /dev/null; then
        echo "[INFO] Detected Fedora. Using dnf..."
        sudo dnf install -y wget
    elif command -v pacman &> /dev/null; then
        echo "[INFO] Detected Arch Linux. Using pacman..."
        sudo pacman -S --noconfirm wget
    elif command -v zypper &> /dev/null; then
        echo "[INFO] Detected openSUSE. Using zypper..."
        sudo zypper install -y wget
    elif command -v brew &> /dev/null; then
        echo "[INFO] Detected macOS with Homebrew. Using brew..."
        brew install wget
    else
        echo "[ERROR] Cannot install wget. Please install it manually and rerun this script." >&2
        return 1
    fi

    # Verify installation
    if command -v wget &> /dev/null; then
        echo "[OK] wget installed successfully."
        return 0
    else
        echo "[ERROR] wget installation failed." >&2
        return 1
    fi
}

# Function to download a file with wget
download_file() {
    local url=$1
    local dest=$2
    local filename=$(basename "$dest")
    
    echo "Downloading: $filename"
    echo "  From: $url"
    echo "  To:   $dest"
    
    # wget options:
    # -c  : resume broken downloads
    # -q  : quiet mode (remove for verbose)
    # --show-progress : show progress bar
    # --tries=3 : retry up to 3 times
    if wget -c --tries=3 --show-progress -O "$dest" "$url"; then
        echo "[OK] Successfully downloaded: $filename"
        return 0
    else
        echo "[ERROR] Failed to download: $filename" >&2
        return 1
    fi
}

# Main script execution
main() {
    echo "=========================================="
    echo "Pi Repository File Downloader"
    echo "=========================================="
    
    # Ensure wget is available
    if ! ensure_wget; then
        echo "[ERROR] Cannot proceed without wget. Exiting." >&2
        exit 1
    fi
    
    echo ""
    echo "Creating download directory: $DOWNLOAD_DIR"
    mkdir -p "$DOWNLOAD_DIR"
    
    echo ""
    echo "Starting downloads..."
    echo "------------------------------------------"
    
    # Download both files
    download_file "$URL1" "$DOWNLOAD_DIR/output.txt"
    status1=$?
    
    download_file "$URL2" "$DOWNLOAD_DIR/state.pkl"
    status2=$?
    
    echo "------------------------------------------"
    echo ""
    
    # Summary
    if [ $status1 -eq 0 ] && [ $status2 -eq 0 ]; then
        echo "[SUCCESS] All files downloaded successfully!"
        echo "Files are located in: $DOWNLOAD_DIR"
        ls -lh "$DOWNLOAD_DIR"
        exit 0
    else
        echo "[ERROR] Some files failed to download." >&2
        [ $status1 -ne 0 ] && echo "  - output.txt: FAILED" >&2
        [ $status2 -ne 0 ] && echo "  - state.pkl: FAILED" >&2
        exit 1
    fi
}

# Run main function
main