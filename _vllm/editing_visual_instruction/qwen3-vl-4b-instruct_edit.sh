# MODEL=qwen3-vl-4b-instruct
# BASE_URL=http://localhost:8080/v1
# API_KEY=vllm-openai-key

# jq -r '[.instruction_visual] | @tsv' \
# data/visual_instruction/nouhin_data_20260325.jsonl |
# head -n 20 |
# while IFS=$'\t' read -r instruction_visual; do
#     org_img_file="${instruction_visual%.*}.png"
#     python _vllm/edit_images_by_visual_instruction.py \
#         --model "$MODEL" \
#         --base_url "$BASE_URL" \
#         --api_key "$API_KEY" \
#         --org_img_file "$org_img_file"
# done

MODEL=qwen3-vl-4b-instruct
BASE_URL=http://localhost:8080/v1
API_KEY=vllm-openai-key

VISUAL_JSONL="data/visual_instruction/nouhin_data_20260325.jsonl"
TEXT_JSONL="data/text_instruction/nouhin_data_reviewer1_20260212.jsonl"

while IFS=$'\t' read -r key instruction_visual; do
    if [ -z "$instruction_visual" ] || [ "$instruction_visual" = "null" ]; then
        echo "skip: missing instruction_visual for key=$key" >&2
        continue
    fi

    org_img_file="${instruction_visual%.*}.png"

    python _vllm/edit_images_by_visual_instruction.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --org_img_file "$org_img_file"

done < <(
    jq -rn \
      --slurpfile visual "$VISUAL_JSONL" \
      --slurpfile text "$TEXT_JSONL" '
        ($visual | map({key: .key, value: .instruction_visual}) | from_entries) as $vmap
        | $text[0:20][]
        | [.key, ($vmap[.key] // null)]
        | @tsv
      '
)