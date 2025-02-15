#!/bin/bash

resolve_ip() {
  subdomain="$1"
  ips=$(dig +short "$subdomain" A 2>/dev/null)
  if [[ -z "$ips" ]]; then
    echo "N/A"  # IP field is "N/A"
  else
    echo "$ips" | tr '\n' ',' | sed 's/,$//'
  fi
}

./subfinder -d "$1" -silent | while read -r line; do
  subdomain=$(echo "$line" | awk '{print $1}')
  subdomain=$(echo "$subdomain" | tr -d '[:space:]')
  status="Unresolvable" # Status is "Unresolvable"

  ips=$(resolve_ip "$subdomain")

  if [[ "$ips" == "N/A" ]]; then # Check for "N/A"
      original_line="$subdomain | $status | N/A" # IP field is "N/A"
      echo "$subdomain,$status,N/A" # IP field is "N/A" for Prometheus
  elif [[ "$ips" == *"."* ]]; then
      original_line="$subdomain | Alive | $ips" # Status is "Alive"
      echo "$subdomain,Alive,$ips" # Status is "Alive" for Prometheus
  else
      cname="$ips"
      resolved_ip=$(dig +short "$cname" A 2>/dev/null)

      if [[ -z "$resolved_ip" ]]; then
          original_line="$subdomain | Unresolvable | $cname" # Status is "Unresolvable"
          echo "$subdomain,Unresolvable,$cname" # Status is "Unresolvable" for Prometheus
      else
          original_line="$subdomain | Alive | $resolved_ip ($cname)" # Status is "Alive"
          echo "$subdomain,Alive,$resolved_ip ($cname)" # Status is "Alive" for Prometheus
      fi
  fi
  echo "$original_line" # Print the original line for the web app
done
