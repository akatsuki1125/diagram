MODEL=qwen3-vl-30b-a3b-instruct
BASE_URL=http://localhost:8080/v1
API_KEY=vllm-openai-key

jq -r '[.edit_instruction, .org_image_name] | @tsv' \
data/text_instruction/nouhin_data_reviewer1_20260212.jsonl |
head -n 20 |
while IFS=$'\t' read -r edit_instruction org_img_file; do
    python _vllm/edit_images_by_text_instruction.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --edit_instruction "$edit_instruction" \
        --org_img_file "$org_img_file"
done