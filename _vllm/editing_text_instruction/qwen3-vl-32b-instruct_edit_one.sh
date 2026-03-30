MODEL=qwen3-vl-32b-instruct
BASE_URL=http://localhost:8080/v1
API_KEY=vllm-openai-key

python - <<'PY' |
import json
path='data/text_instruction/nouhin_data_reviewer1_20260212.jsonl'
target='00000105_UPDATE_1_edit_0'
with open(path, 'r') as f:
    for line in f:
        obj=json.loads(line)
        if obj.get('key')==target:
            # TSV: edit_instruction \t org_image_name
            print(obj.get('edit_instruction',''), obj.get('org_image_name',''), sep='\t')
            break
PY
while IFS=$'\t' read -r edit_instruction org_img_file; do
    echo "processing key=00000105_UPDATE_1_edit_0 org_image_name=${org_img_file}"
    python _vllm/edit_images_by_text_instruction.py \
        --model "$MODEL" \
        --base_url "$BASE_URL" \
        --api_key "$API_KEY" \
        --edit_instruction "$edit_instruction" \
        --org_img_file "$org_img_file"
done
