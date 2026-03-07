#!/usr/bin/env bash
set -Eeuo pipefail

readonly WG_PORT="51820"
readonly WG_NETWORK_PREFIX="24"
readonly KEEPALIVE="25"
readonly OUTPUT_DIR="./wireguard-configs"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  }
}

# name|label|lan_ip|public_endpoint_ip|wg_ip_last_octet
#
# public_endpoint_ip:
# - use real public IP for internet-reachable peers
# - leave empty for local-only peers
#
# label:
# - used in the generated comment above each [Peer]
#
# Example generated comment:
#   # KVM 2 - 76.13.71.178:51820 -> 10.100.0.2/32
#
declare -a NODES=(
  "m4128|Local m4128|192.168.0.109|192.168.0.109|26"
  "m132|Local m132|192.168.0.108|192.168.0.108|25"
  "fedoraair|Local fedoraair|192.168.0.114|192.168.0.114|27"
  "kvm2|KVM 2|76.13.71.178|76.13.71.178|2"
  "kvm4|KVM 4|191.101.70.130|191.101.70.130|4"
  "kvm8|KVM 8|89.116.73.152|89.116.73.152|8"
)

declare -A LABELS=()
declare -A LAN_IPS=()
declare -A ENDPOINT_IPS=()
declare -A WG_IPS=()
declare -A PRIVATE_KEYS=()
declare -A PUBLIC_KEYS=()

parse_nodes() {
  local entry
  local name
  local label
  local lan_ip
  local endpoint_ip
  local wg_last_octet

  for entry in "${NODES[@]}"; do
    IFS='|' read -r name label lan_ip endpoint_ip wg_last_octet <<< "$entry"

    LABELS["$name"]="$label"
    LAN_IPS["$name"]="$lan_ip"
    ENDPOINT_IPS["$name"]="$endpoint_ip"
    WG_IPS["$name"]="10.100.0.${wg_last_octet}"
  done
}

generate_keys() {
  local name
  local private_key
  local public_key

  for name in "${!LABELS[@]}"; do
    private_key="$(wg genkey)"
    public_key="$(printf '%s' "$private_key" | wg pubkey)"

    PRIVATE_KEYS["$name"]="$private_key"
    PUBLIC_KEYS["$name"]="$public_key"
  done
}

write_peer_block() {
  local self_name="$1"
  local peer_name="$2"

  local peer_label="${LABELS[$peer_name]}"
  local peer_lan_ip="${LAN_IPS[$peer_name]}"
  local peer_endpoint_ip="${ENDPOINT_IPS[$peer_name]}"
  local peer_wg_ip="${WG_IPS[$peer_name]}"
  local peer_public_key="${PUBLIC_KEYS[$peer_name]}"

  printf '# %s - %s:%s -> %s/32\n' \
    "$peer_label" \
    "${peer_endpoint_ip:-$peer_lan_ip}" \
    "$WG_PORT" \
    "$peer_wg_ip"

  printf '[Peer]\n'
  printf 'PublicKey = %s\n' "$peer_public_key"
  printf 'AllowedIPs = %s/32\n' "$peer_wg_ip"

  if [[ -n "$peer_endpoint_ip" ]]; then
    printf 'Endpoint = %s:%s\n' "$peer_endpoint_ip" "$WG_PORT"
  fi

  printf 'PersistentKeepalive = %s\n\n' "$KEEPALIVE"
}

write_config() {
  local self_name="$1"
  local file_path="$OUTPUT_DIR/${self_name}.conf"
  local peer_name

  {
    printf '[Interface]\n'
    printf 'PrivateKey = %s\n' "${PRIVATE_KEYS[$self_name]}"
    printf 'ListenPort = %s\n' "$WG_PORT"
    printf 'Address = %s/%s\n\n' "${WG_IPS[$self_name]}" "$WG_NETWORK_PREFIX"

    for peer_name in "${!LABELS[@]}"; do
      [[ "$peer_name" == "$self_name" ]] && continue
      write_peer_block "$self_name" "$peer_name"
    done
  } > "$file_path"
}

write_key_summary() {
  local file_path="$OUTPUT_DIR/keys.txt"
  local name

  {
    for name in "${!LABELS[@]}"; do
      printf '%s\n' "$name"
      printf '  private: %s\n' "${PRIVATE_KEYS[$name]}"
      printf '  public : %s\n' "${PUBLIC_KEYS[$name]}"
      printf '  wg ip  : %s/%s\n\n' "${WG_IPS[$name]}" "$WG_NETWORK_PREFIX"
    done
  } > "$file_path"
}

main() {
  require_cmd wg

  mkdir -p "$OUTPUT_DIR"
  chmod 700 "$OUTPUT_DIR"

  parse_nodes
  generate_keys

  local name
  for name in "${!LABELS[@]}"; do
    write_config "$name"
  done

  write_key_summary

  chmod 600 "$OUTPUT_DIR"/*.conf "$OUTPUT_DIR"/keys.txt

  printf 'Generated configs in: %s\n' "$OUTPUT_DIR"
  printf 'Files:\n'
  ls -1 "$OUTPUT_DIR"
}

main "$@"
