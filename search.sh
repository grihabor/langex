python -m langex -d headers.txt -b 1 -e 2 | jq '.[] | select(.speaks|map(. == "English")|any) | select(.looks_for|map(. == "Russian language exchange")|any)'
