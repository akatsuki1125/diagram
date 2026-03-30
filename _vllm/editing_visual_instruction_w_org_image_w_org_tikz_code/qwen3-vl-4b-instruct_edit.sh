# MODEL=qwen3-vl-4b-instruct
# BASE_URL=http://localhost:8080/v1
# API_KEY=vllm-openai-key

# jq -r '[.instruction_visual, .org_image_name] | @tsv' \
# data/visual_instruction/nouhin_data_20260325.jsonl |
# head -n 20 |
# while IFS=$'\t' read -r instruction_visual org_img_file; do
#     org_img_stem="${org_img_file%.*}"
#     org_tikz_stem="${org_img_stem%%_org_*}"
#     org_tikz_file="data/org_tikz_code/${org_tikz_stem}.tex"
#     if [ ! -f "$org_tikz_file" ]; then
#         echo "skip: missing $org_tikz_file" >&2
#         continue
#     fi
#     original_tikz_code="$(cat "$org_tikz_file")"
#     annotated_img_file="${instruction_visual%.*}.png"
#     python _vllm/edit_images_by_visual_instruction_w_org_image_w_org_tikz_code.py \
#         --model "$MODEL" \
#         --base_url "$BASE_URL" \
#         --api_key "$API_KEY" \
#         --annotated_img_file "${annotated_img_file}"  \
#         --original_tikz_code "$original_tikz_code" \
#         --org_img_file "$org_img_file"
# done


MODEL=qwen3-vl-4b-instruct
BASE_URL=http://localhost:8080/v1
API_KEY=vllm-openai-key

VISUAL_JSONL="data/visual_instruction/nouhin_data_20260325.jsonl"
TEXT_JSONL="data/text_instruction/nouhin_data_reviewer1_20260212.jsonl"

while IFS=$'\t' read -r key org_img_file instruction_visual; do
    if [ -z "$instruction_visual" ] || [ "$instruction_visual" = "null" ]; then
        echo "skip: missing instruction_visual for key=$key" >&2
        continue
    fi

    org_img_stem="${org_img_file%.*}"
    org_tikz_stem="${org_img_stem%%_org_*}"
    org_tikz_file="data/org_tikz_code/${org_tikz_stem}.tex"

    if [ ! -f "$org_tikz_file" ]; then
        echo "skip: missing $org_tikz_file" >&2
        continue
    fi

    original_tikz_code="$(cat "$org_tikz_file")"
    annotated_img_file="${instruction_visual%.*}.png"

    python _vllm/edit_images_by_visual_instruction_w_org_image_w_org_tikz_code.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --annotated_img_file "$annotated_img_file" \
        --original_tikz_code "$original_tikz_code" \
        --org_img_file "$org_img_file"

done < <(
    jq -rn \
      --slurpfile visual "$VISUAL_JSONL" \
      --slurpfile text "$TEXT_JSONL" '
        # visual側から key -> instruction_visual の辞書を作る
        ($visual | map({key: .key, value: .instruction_visual}) | from_entries) as $vmap
        # text側の先頭20件を処理
        | $text[0:20][]
        | [.key, .org_image_name, ($vmap[.key] // null)]
        | @tsv
      '
)