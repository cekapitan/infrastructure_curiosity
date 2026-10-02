#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the Infrastructure Curiosity gate.
# Installs the toolchain required by `make gate`: Terraform, TFLint,
# ShellCheck, and Gitleaks. Pinned to match .github/workflows/ci.yml.
set -euo pipefail

TERRAFORM_VERSION="1.15.8"
TFLINT_VERSION="0.64.0"
GITLEAKS_VERSION="8.30.1"

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) TF_ARCH="amd64"; GL_ARCH="x64" ;;
  aarch64 | arm64) TF_ARCH="arm64"; GL_ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

BIN_DIR="/usr/local/bin"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log() { printf '==> %s\n' "$1"; }

have_version() {
  # have_version <command> <expected-substring>
  command -v "$1" >/dev/null 2>&1 && "$1" --version 2>&1 | grep -q "$2"
}

log "apt: shellcheck"
if ! command -v shellcheck >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y --no-install-recommends shellcheck unzip curl ca-certificates
fi

log "terraform ${TERRAFORM_VERSION}"
if ! have_version terraform "v${TERRAFORM_VERSION}"; then
  curl -fsSL -o "$TMP_DIR/terraform.zip" \
    "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${TF_ARCH}.zip"
  unzip -o -q "$TMP_DIR/terraform.zip" -d "$TMP_DIR"
  sudo install -m 0755 "$TMP_DIR/terraform" "$BIN_DIR/terraform"
fi

log "tflint ${TFLINT_VERSION}"
if ! have_version tflint "${TFLINT_VERSION}"; then
  curl -fsSL -o "$TMP_DIR/tflint.zip" \
    "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_${TF_ARCH}.zip"
  unzip -o -q "$TMP_DIR/tflint.zip" -d "$TMP_DIR/tflint"
  sudo install -m 0755 "$TMP_DIR/tflint/tflint" "$BIN_DIR/tflint"
fi

log "gitleaks ${GITLEAKS_VERSION}"
if ! have_version gitleaks "${GITLEAKS_VERSION}"; then
  curl -fsSL -o "$TMP_DIR/gitleaks.tar.gz" \
    "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${GL_ARCH}.tar.gz"
  tar -xzf "$TMP_DIR/gitleaks.tar.gz" -C "$TMP_DIR" gitleaks
  sudo install -m 0755 "$TMP_DIR/gitleaks" "$BIN_DIR/gitleaks"
fi

log "installed versions"
set +o pipefail
terraform version | head -1
tflint --version | head -1
shellcheck --version | sed -n 's/^version: //p'
gitleaks version
python3 --version
set -o pipefail
