#!/bin/sh

set -eu

CDPATH=''
export CDPATH
repo_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    printf '%s\n' "Required tool is missing: $1" >&2
    exit 1
  }
}

require_tool python3
require_tool terraform
require_tool tflint
require_tool shellcheck

printf '%s\n' "==> repository contracts"
python3 -m unittest discover -s tests -p 'test_*.py' -v

printf '%s\n' "==> Terraform formatting"
terraform fmt -check -recursive -diff

terraform_dirs="$(mktemp "${TMPDIR:-/tmp}/infrastructure-curiosity-tfdirs.XXXXXX")"
shell_files="$(mktemp "${TMPDIR:-/tmp}/infrastructure-curiosity-shell.XXXXXX")"
cleanup() {
  rm -f "$terraform_dirs" "$shell_files"
}
trap cleanup EXIT HUP INT TERM

find examples -type f -name '*.tf' -exec dirname {} \; | LC_ALL=C sort -u >"$terraform_dirs"

while IFS= read -r terraform_dir; do
  [ -n "$terraform_dir" ] || continue
  printf '%s\n' "==> Terraform init: $terraform_dir"
  TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true \
    terraform -chdir="$terraform_dir" init -backend=false -input=false -no-color
  terraform -chdir="$terraform_dir" validate -no-color
  if find "$terraform_dir" -type f -name '*.tftest.hcl' | grep -q .; then
    printf '%s\n' "==> Terraform mocked tests: $terraform_dir"
    TF_IN_AUTOMATION=1 AWS_EC2_METADATA_DISABLED=true \
      terraform -chdir="$terraform_dir" test -no-color
  fi
done <"$terraform_dirs"

printf '%s\n' "==> TFLint"
tflint --recursive --config "$repo_root/.tflint.hcl" --no-color

printf '%s\n' "==> ShellCheck"
find automation scripts -type f -name '*.sh' -print >"$shell_files"
find .codex/bin -type f -print >>"$shell_files"
LC_ALL=C sort -u "$shell_files" -o "$shell_files"
if [ -s "$shell_files" ]; then
  xargs shellcheck <"$shell_files"
fi

printf '%s\n' "==> secret scan"
if [ "${SKIP_GITLEAKS:-0}" = "1" ]; then
  printf '%s\n' "Gitleaks is handled by the separate CI action."
else
  require_tool gitleaks
  gitleaks dir --no-banner --no-color --redact "$repo_root"
fi

if find . -type f \( -name '*.tfstate' -o -name '*.tfstate.*' \) -print | grep -q .; then
  printf '%s\n' "Terraform state was created; refusing to pass the gate." >&2
  exit 1
fi

printf '%s\n' "All repository gates passed. No infrastructure was provisioned."
