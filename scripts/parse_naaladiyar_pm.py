import json
import re

def parse_naladiyar(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    # Find the end of each verse (first occurrence of line ending in number N)
    v_end_indices = {}
    for i, line in enumerate(lines):
        match = re.search(r'\s+(\d+)$', line)
        if match:
            num = int(match.group(1))
            if num not in v_end_indices and 1 <= num <= 400:
                v_end_indices[num] = i

    results = []
    for n in range(1, 401):
        if n not in v_end_indices:
            print(f"Verse {n} not found!")
            continue
            
        v_end = v_end_indices[n]
        # Verse is the 4 lines ending at v_end
        v_start = max(0, v_end - 3)
        verse_lines = lines[v_start : v_end + 1]
        verse_text = "\n".join([re.sub(r'\s+\d+$', '', l).strip() for l in verse_lines])
        
        # Explanation starts after v_end
        # It ends before the start of the next verse (v_end_indices[n+1] - 3)
        if n < 400:
            next_v_start = v_end_indices[n+1] - 3
        else:
            next_v_start = len(lines)
            
        raw_exp_lines = lines[v_end + 1 : next_v_start]
        
        # Clean up explanation:
        # 1. Stop at the first dashed line if it exists
        exp_lines = []
        for l in raw_exp_lines:
            if re.match(r'^-+$', l):
                break
            # Skip chapter headers/titles (usually don't have the verse number at the end)
            if 'வியல்' in l or '/' in l: continue
            if re.match(r'^\d+\.', l) and not re.search(r'\s+\d+$', l): continue
            exp_lines.append(l)
            
        explanation_text = " ".join(exp_lines)
        # Remove trailing verse number if present
        explanation_text = re.sub(r'\s+' + str(n) + r'$', '', explanation_text).strip()
        # Remove any other trailing numbers
        explanation_text = re.sub(r'\s+\d+$', '', explanation_text).strip()
        
        results.append({
            "verse": verse_text,
            "explanation": explanation_text
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    return len(results)

if __name__ == "__main__":
    count = parse_naladiyar('naladiyar_text.txt', 'naladiyar.jsonl')
    print(f"Successfully created naladiyar.jsonl with {count} entries.")
