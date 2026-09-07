import openpyxl

wb = openpyxl.load_workbook('DGAD_Literature_Review.xlsx')
ws = wb.active

# Fix the new papers (rows 15-21)
fixes = {
    15: 'DiscoUQ (Logistic Regression on Disagreement Structure Features)',
    16: 'CASCADE (3-Tier: Regex/Entropy -> BGE Embedding + Llama3 Fallback -> Output Pattern Filtering)',
    17: 'JailGuard (Mutation-based Discrepancy Detection via KL Divergence)',
    18: 'PromptForest (Weighted Soft Voting Ensemble + Uncertainty Scoring via Prediction Std Dev)',
    19: 'ZEDD (Embedding Drift via Cosine Similarity + GMM/KDE Ensemble Flagging)',
    20: 'SmoothLLM (Randomized Smoothing: Character Perturbation + Majority Vote Aggregation)',
    21: 'FJD (Free Jailbreak Detection: Affirmative Prefix + Temperature-Scaled Logit Confidence)',
}

for row_idx, new_method in fixes.items():
    ws.cell(row=row_idx, column=6, value=new_method)
    print(f'Row {row_idx}: Updated to "{new_method}"')

wb.save('DGAD_Literature_Review.xlsx')
print('Done!')