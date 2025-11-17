#!/bin/bash
# Example: Using model configuration file for report generation

task_input_file=../test_data/qa_test.jsonl
output_folder=project/report/config_default/qa_test
mkdir -p ${output_folder}
task_output_file=${output_folder}/result.jsonl
done_file=${output_folder}/done.txt

echo "=== Report Generation Examples with Model Configuration ==="
echo ""

# Example 1: Use default models from config with SerpAPI
echo "Example 1: Using default models from model_config.yaml"
python engine.py \
  --filename $task_input_file \
  --output-filename $task_output_file \
  --done-flag-file $done_file \
  --engine-backend serpapi \
  --mode report

# Example 2: Use Gemini preset
# Uncomment to run:
# echo "Example 2: Using 'gemini' preset"
# mkdir -p ${output_folder}_gemini
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_gemini/result.jsonl \
#   --done-flag-file ${output_folder}_gemini/done.txt \
#   --preset gemini \
#   --engine-backend serpapi \
#   --mode report

# Example 3: Use specific model with custom selector/summarizer
# Uncomment to run:
# echo "Example 3: GPT-4o with Gemini selector and summarizer"
# mkdir -p ${output_folder}_custom
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_custom/result.jsonl \
#   --done-flag-file ${output_folder}_custom/done.txt \
#   --model gpt-4o \
#   --selector-model gemini-2.0-flash \
#   --summarizer-model gemini-2.0-flash \
#   --engine-backend serpapi \
#   --mode report

# Example 4: Economy preset with SearXNG (self-hosted search)
# Uncomment to run:
# echo "Example 4: Using 'economy' preset with SearXNG"
# mkdir -p ${output_folder}_economy
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_economy/result.jsonl \
#   --done-flag-file ${output_folder}_economy/done.txt \
#   --preset economy \
#   --engine-backend searxng \
#   --mode report

# Example 5: Premium preset for high-quality reports
# Uncomment to run:
# echo "Example 5: Using 'premium' preset (Claude + GPT-4o)"
# mkdir -p ${output_folder}_premium
# python engine.py \
#   --filename $task_input_file \
#   --output-filename ${output_folder}_premium/result.jsonl \
#   --done-flag-file ${output_folder}_premium/done.txt \
#   --preset premium \
#   --engine-backend serpapi \
#   --mode report
