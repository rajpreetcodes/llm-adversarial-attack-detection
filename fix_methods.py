import openpyxl

wb = openpyxl.load_workbook('DGAD_Literature_Review.xlsx')
ws = wb.active

fixes = {
    3: 'Ignore Previous Prompt / Goal Hijacking',
    4: 'AutoDAN (Hierarchical Genetic Algorithm)',
    6: 'Llama Guard (Instruction-tuned Safety Classifier)',
    7: 'Prompt Injection Formal Framework (Threat Model + Benchmark)',
    8: 'IndirectPromptInjection Benchmark (5 Task Scenarios)',
    9: 'Windowed Perplexity Filtering (GPT-2 Reference LM)',
    10: 'Baseline Defense Evaluation Harness (Perplexity + Paraphrasing + Retokenization)',
    11: 'Guardrail Benchmarking Harness (Multi-dataset, FPR-controlled)',
    12: 'InjecGuard (MOF Fine-tuning Strategy)',
    13: 'GradSafe (Safety-Critical Gradient Analysis)',
    14: 'Adaptive Evasion via Character Injection + AML Obfuscation',
}

for row_idx, new_method in fixes.items():
    ws.cell(row=row_idx, column=6, value=new_method)
    print(f'Row {row_idx}: Updated to "{new_method}"')

wb.save('DGAD_Literature_Review.xlsx')
print('Done!')