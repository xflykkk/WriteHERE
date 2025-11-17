#!/bin/bash
# Example: Using model configuration file for story generation

task_input_file=../test_data/meta_fiction.jsonl
output_folder=project/story/config_default/meta_fiction
mkdir -p ${output_folder}
task_output_file=${output_folder}/result.jsonl
done_file=${output_folder}/done.txt

echo "=== Story Generation Examples with Model Configuration ==="
echo ""

# Example 1: Use default model from config
echo "Example 1: Using default model from model_config.yaml"
python engine.py \
  --filename $task_input_file \
  --output-filename $task_output_file \
  --done-flag-file $done_file \
  --mode story

# Example 2: Use a specific model (overrides config)
# Uncomment to run:
# echo "Example 2: Using specific model (Claude 3.7 Sonnet)"
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_claude/result.jsonl \
#   --done-flag-file ${output_folder}_claude/done.txt \
#   --model claude-3-7-sonnet-20250219 \
#   --mode story

# Example 3: Use a preset
# Uncomment to run:
# echo "Example 3: Using 'premium' preset"
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_premium/result.jsonl \
#   --done-flag-file ${output_folder}_premium/done.txt \
#   --preset premium \
#   --mode story

# Example 4: Use 'economy' preset for cost-effective generation
# Uncomment to run:
# echo "Example 4: Using 'economy' preset (GPT-4o-mini)"
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_economy/result.jsonl \
#   --done-flag-file ${output_folder}_economy/done.txt \
#   --preset economy \
#   --mode story
