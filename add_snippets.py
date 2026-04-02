import os
import csv

# Define New Snippets

snippets = []

# OFF BY ONE
snippets.append({
    'type': 'off_by_one',
    'id': 11,
    'buggy_code': """public class OffByOneBug011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length; i > 0; i--) {
            System.out.println(arr[i]);
        }
    }
}""",
    'fixed_code': """public class OffByOneFix011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length - 1; i >= 0; i--) {
            System.out.println(arr[i]);
        }
    }
}""",
    'notes': "reverse iteration from arr.length instead of length - 1"
})

snippets.append({
    'type': 'off_by_one',
    'id': 12,
    'buggy_code': """public class OffByOneBug012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while(left <= right.length) {
            left++;
        }
    }
}""",
    'fixed_code': """public class OffByOneFix012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while(left < right.length) {
            left++;
        }
    }
}""",
    'notes': "while loop boundary condition using <="
})

snippets.append({
    'type': 'off_by_one',
    'id': 13,
    'buggy_code': """public class OffByOneBug013 {
    public void iterateRows(int[][] matrix) {
        for (int r = 0; r <= matrix.length; r++) {
            matrix[r][0] = 1;
        }
    }
}""",
    'fixed_code': """public class OffByOneFix013 {
    public void iterateRows(int[][] matrix) {
        for (int r = 0; r < matrix.length; r++) {
            matrix[r][0] = 1;
        }
    }
}""",
    'notes': "2d array row iteration using <="
})

snippets.append({
    'type': 'off_by_one',
    'id': 14,
    'buggy_code': """public class OffByOneBug014 {
    public void iterateCols(int[][] matrix) {
        for (int c = 0; c <= matrix[0].length; c++) {
            matrix[0][c] = 1;
        }
    }
}""",
    'fixed_code': """public class OffByOneFix014 {
    public void iterateCols(int[][] matrix) {
        for (int c = 0; c < matrix[0].length; c++) {
            matrix[0][c] = 1;
        }
    }
}""",
    'notes': "2d array col iteration using <="
})

snippets.append({
    'type': 'off_by_one',
    'id': 15,
    'buggy_code': """public class OffByOneBug015 {
    public void skipByTwo(int[] arr) {
        for (int i = 0; i <= arr.length; i += 2) {
            System.out.println(arr[i]);
        }
    }
}""",
    'fixed_code': """public class OffByOneFix015 {
    public void skipByTwo(int[] arr) {
        for (int i = 0; i < arr.length; i += 2) {
            System.out.println(arr[i]);
        }
    }
}""",
    'notes': "skip by 2 iteration using <="
})

# INCORRECT CONDITIONAL OPERATOR
snippets.append({
    'type': 'incorrect_conditional_operator',
    'id': 11,
    'buggy_code': """public class IncorrectConditionalBug011 {
    public void checkStatus(boolean status) {
        while (status = true) {
            System.out.println("Running");
            break;
        }
    }
}""",
    'fixed_code': """public class IncorrectConditionalFix011 {
    public void checkStatus(boolean status) {
        while (status == true) {
            System.out.println("Running");
            break;
        }
    }
}""",
    'notes': "assignment inside while condition instead of equality"
})

snippets.append({
    'type': 'incorrect_conditional_operator',
    'id': 12,
    'buggy_code': """public class IncorrectConditionalBug012 {
    public void checkLength(int len) {
        if (len = 0) {
            return;
        }
    }
}""",
    'fixed_code': """public class IncorrectConditionalFix012 {
    public void checkLength(int len) {
        if (len == 0) {
            return;
        }
    }
}""",
    'notes': "assignment of integer 0 inside if condition"
})

snippets.append({
    'type': 'incorrect_conditional_operator',
    'id': 13,
    'buggy_code': """public class IncorrectConditionalBug013 {
    public void validateUser(Object user) {
        if (user = null) {
            throw new IllegalArgumentException();
        }
    }
}""",
    'fixed_code': """public class IncorrectConditionalFix013 {
    public void validateUser(Object user) {
        if (user == null) {
            throw new IllegalArgumentException();
        }
    }
}""",
    'notes': "assignment of null object inside if loop"
})

snippets.append({
    'type': 'incorrect_conditional_operator',
    'id': 14,
    'buggy_code': """public class IncorrectConditionalBug014 {
    public void multipleChecks(int a, int b) {
        if (a > 5 && b = 10) {
            System.out.println("Win");
        }
    }
}""",
    'fixed_code': """public class IncorrectConditionalFix014 {
    public void multipleChecks(int a, int b) {
        if (a > 5 && b == 10) {
            System.out.println("Win");
        }
    }
}""",
    'notes': "assignment operator mixed in logical && expression"
})

snippets.append({
    'type': 'incorrect_conditional_operator',
    'id': 15,
    'buggy_code': """public class IncorrectConditionalBug015 {
    public void parseVal(int val) {
        int z = (val = 5) ? 1 : 0;
    }
}""",
    'fixed_code': """public class IncorrectConditionalFix015 {
    public void parseVal(int val) {
        int z = (val == 5) ? 1 : 0;
    }
}""",
    'notes': "ternary condition with assignment instead of equality"
})

# ARRAY LENGTH INDEX MISUSE
snippets.append({
    'type': 'array_length_index_misuse',
    'id': 11,
    'buggy_code': """public class ArrayIndexBug011 {
    public int getCombinedEnd(int[] arr1, int[] arr2) {
        int[] combined = new int[arr1.length + arr2.length];
        return combined[combined.length];
    }
}""",
    'fixed_code': """public class ArrayIndexFix011 {
    public int getCombinedEnd(int[] arr1, int[] arr2) {
        int[] combined = new int[arr1.length + arr2.length];
        return combined[combined.length - 1];
    }
}""",
    'notes': "accessing end of dynamically combined array length directly"
})

snippets.append({
    'type': 'array_length_index_misuse',
    'id': 12,
    'buggy_code': """public class ArrayIndexBug012 {
    public int[] getLastRow(int[][] matrix) {
        return matrix[matrix.length];
    }
}""",
    'fixed_code': """public class ArrayIndexFix012 {
    public int[] getLastRow(int[][] matrix) {
        return matrix[matrix.length - 1];
    }
}""",
    'notes': "accessing matrix.length as row index"
})

snippets.append({
    'type': 'array_length_index_misuse',
    'id': 13,
    'buggy_code': """public class ArrayIndexBug013 {
    public int getLastSize(int[] sizes) {
        return sizes[sizes.length] * 2;
    }
}""",
    'fixed_code': """public class ArrayIndexFix013 {
    public int getLastSize(int[] sizes) {
        return sizes[sizes.length - 1] * 2;
    }
}""",
    'notes': "fetching size inside arithmetic expression ending at length"
})

snippets.append({
    'type': 'array_length_index_misuse',
    'id': 14,
    'buggy_code': """public class ArrayIndexBug014 {
    public int fetchBonus(int[] bonuses) {
        return bonuses[bonuses.length] + 5;
    }
}""",
    'fixed_code': """public class ArrayIndexFix014 {
    public int fetchBonus(int[] bonuses) {
        return bonuses[bonuses.length - 1] + 5;
    }
}""",
    'notes': "direct out of bounds in return addition expression"
})

snippets.append({
    'type': 'array_length_index_misuse',
    'id': 15,
    'buggy_code': """public class ArrayIndexBug015 {
    public void swapEnds(int[] arr) {
        int temp = arr[0];
        arr[0] = arr[arr.length];
        arr[arr.length] = temp;
    }
}""",
    'fixed_code': """public class ArrayIndexFix015 {
    public void swapEnds(int[] arr) {
        int temp = arr[0];
        arr[0] = arr[arr.length - 1];
        arr[arr.length - 1] = temp;
    }
}""",
    'notes': "swapping first and last elements uses arr.length directly"
})

# CLEAN
cleans = [
    {
        'id': 7,
        'code': """public class Clean007 {
    public void readMax(int[] arr) {
        int max = arr.length;
        int idx = 0;
        while(idx < max) {
            System.out.println(arr[idx]);
            idx++;
        }
    }
}""",
        'notes': "standard while loop with variables limit"
    },
    {
        'id': 8,
        'code': """public class Clean008 {
    public int calculateSum(int[] arr) {
        int sum = 0;
        for(int num : arr) {
            sum += num;
        }
        return sum;
    }
}""",
        'notes': "enhanced for loop calculating sum without indices"
    },
    {
        'id': 9,
        'code': """public class Clean009 {
    public boolean checkReady(boolean isReady) {
        if (isReady == true) {
            return true;
        }
        return false;
    }
}""",
        'notes': "proper equality check against boolean true"
    },
    {
        'id': 10,
        'code': """public class Clean010 {
    public int getMiddleElement(int[] arr) {
        return arr[arr.length / 2];
    }
}""",
        'notes': "safe retrieval using arr.length divided by 2"
    },
    {
        'id': 11,
        'code': """public class Clean011 {
    public void loopFromOne(int[] arr) {
        for(int i = 1; i < arr.length; i++) {
            arr[i] = arr[i - 1] + 1;
        }
    }
}""",
        'notes': "starts loop at 1 ending at < array length safely"
    }
]

import pathlib

base_path = pathlib.Path('data/ml/')

def write_and_record(csv_writer, pair_num: int, s: dict):
    # Determine directory
    cat_dir = s['type']
    buggy_path = base_path / 'raw_snippets' / cat_dir / 'buggy' / f"{cat_dir.replace('_', ' ').title().replace(' ', '')}Bug{s['id']:03d}.java"
    fix_path = base_path / 'raw_snippets' / cat_dir / 'fixed' / f"{cat_dir.replace('_', ' ').title().replace(' ', '')}Fix{s['id']:03d}.java"
    
    # Write Buggy
    buggy_path.parent.mkdir(parents=True, exist_ok=True)
    with open(buggy_path, 'w', encoding='utf-8') as f:
        f.write(s['buggy_code'])
        
    bug_flags = {'off_by_one': '0', 'incorrect_conditional_operator': '0', 'array_length_index_misuse': '0'}
    bug_flags[s['type']] = '1'
    
    buggy_id = f"{cat_dir.split('_')[0]}_{cat_dir.split('_')[1] if 'off' in cat_dir else 'cond' if 'cond' in cat_dir else 'index'}_bug_{s['id']:03d}"
    
    label_map = {
        'off_by_one': 'OFF_BY_ONE_LOOP_BOUNDARY',
        'incorrect_conditional_operator': 'INCORRECT_CONDITIONAL_OPERATOR',
        'array_length_index_misuse': 'ARRAY_LENGTH_INDEX_MISUSE'
    }
    
    csv_writer.writerow({
        'snippet_id': buggy_id,
        'file_path': str(buggy_path).replace('\\', '/'),
        'language': 'java',
        'primary_label': label_map[s['type']],
        'is_clean': '0',
        'has_off_by_one': bug_flags['off_by_one'],
        'has_incorrect_conditional': bug_flags['incorrect_conditional_operator'],
        'has_array_length_index_misuse': bug_flags['array_length_index_misuse'],
        'pair_group': f'pair_{pair_num:03d}',
        'pair_role': 'buggy',
        'source_type': 'manual_curated',
        'notes': s['notes']
    })

    # Write Fixed
    fix_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fix_path, 'w', encoding='utf-8') as f:
        f.write(s['fixed_code'])
        
    fix_id = f"{cat_dir.split('_')[0]}_{cat_dir.split('_')[1] if 'off' in cat_dir else 'cond' if 'cond' in cat_dir else 'index'}_fix_{s['id']:03d}"
    
    csv_writer.writerow({
        'snippet_id': fix_id,
        'file_path': str(fix_path).replace('\\', '/'),
        'language': 'java',
        'primary_label': 'NO_ISSUE',
        'is_clean': '1',
        'has_off_by_one': '0',
        'has_incorrect_conditional': '0',
        'has_array_length_index_misuse': '0',
        'pair_group': f'pair_{pair_num:03d}',
        'pair_role': 'fixed',
        'source_type': 'manual_curated',
        'notes': 'fixed: ' + s['notes']
    })

csv_file = base_path / 'metadata' / 'snippet_index.csv'

with open(csv_file, 'a', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'snippet_id','file_path','language','primary_label','is_clean',
        'has_off_by_one','has_incorrect_conditional','has_array_length_index_misuse',
        'pair_group','pair_role','source_type','notes'
    ])
    
    # Let's say pairs stopped around 030 in the original file. Let's resume from 031 safe limit.
    # From snippet index it ended at 030.
    curr_pair = 31
    for s in snippets:
        write_and_record(writer, curr_pair, s)
        curr_pair += 1

    for c in cleans:
        clean_path = base_path / 'raw_snippets' / 'clean' / f"Clean{c['id']:03d}.java"
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        with open(clean_path, 'w', encoding='utf-8') as cf:
            cf.write(c['code'])
            
        writer.writerow({
            'snippet_id': f"clean_{c['id']:03d}",
            'file_path': str(clean_path).replace('\\', '/'),
            'language': 'java',
            'primary_label': 'NO_ISSUE',
            'is_clean': '1',
            'has_off_by_one': '0',
            'has_incorrect_conditional': '0',
            'has_array_length_index_misuse': '0',
            'pair_group': '',
            'pair_role': 'clean',
            'source_type': 'manual_curated',
            'notes': c['notes']
        })

print("Generated all files and updated index.")
