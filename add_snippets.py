import csv
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ----------------------------
# Project path detection
# ----------------------------

THIS_DIR = Path(__file__).resolve().parent

if (THIS_DIR / "data" / "ml").exists():
    PROJECT_ROOT = THIS_DIR
elif (THIS_DIR.parent / "data" / "ml").exists():
    PROJECT_ROOT = THIS_DIR.parent
else:
    # fallback: assume script is inside backend/
    PROJECT_ROOT = THIS_DIR.parent

BASE_PATH = PROJECT_ROOT / "data" / "ml"
CSV_FILE = BASE_PATH / "metadata" / "snippet_index.csv"

FIELDNAMES = [
    "snippet_id",
    "file_path",
    "language",
    "primary_label",
    "is_clean",
    "has_off_by_one",
    "has_incorrect_conditional",
    "has_array_length_index_misuse",
    "pair_group",
    "pair_role",
    "source_type",
    "notes",
]

LABEL_MAP = {
    "off_by_one": "OFF_BY_ONE_LOOP_BOUNDARY",
    "incorrect_conditional_operator": "INCORRECT_CONDITIONAL_OPERATOR",
    "array_length_index_misuse": "ARRAY_LENGTH_INDEX_MISUSE",
}

PREFIX_MAP = {
    "off_by_one": "off_by",
    "incorrect_conditional_operator": "incorrect_cond",
    "array_length_index_misuse": "array_index",
}

# ----------------------------
# Existing snippet bank restored
# + new array snippets 016-030
# ----------------------------

PAIR_SNIPPETS: List[Dict[str, str]] = [
    # OFF BY ONE 011-015
    {
        "type": "off_by_one",
        "id": 11,
        "buggy_class_name": "OffByOneBug011",
        "fixed_class_name": "OffByOneFix011",
        "buggy_code": """public class OffByOneBug011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length; i > 0; i--) {
            System.out.println(arr[i]);
        }
    }
}""",
        "fixed_code": """public class OffByOneFix011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length - 1; i >= 0; i--) {
            System.out.println(arr[i]);
        }
    }
}""",
        "notes": "reverse iteration from arr.length instead of length - 1",
    },
    {
        "type": "off_by_one",
        "id": 12,
        "buggy_class_name": "OffByOneBug012",
        "fixed_class_name": "OffByOneFix012",
        "buggy_code": """public class OffByOneBug012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while(left <= right.length) {
            left++;
        }
    }
}""",
        "fixed_code": """public class OffByOneFix012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while(left < right.length) {
            left++;
        }
    }
}""",
        "notes": "while loop boundary condition using <=",
    },
    {
        "type": "off_by_one",
        "id": 13,
        "buggy_class_name": "OffByOneBug013",
        "fixed_class_name": "OffByOneFix013",
        "buggy_code": """public class OffByOneBug013 {
    public void iterateRows(int[][] matrix) {
        for (int r = 0; r <= matrix.length; r++) {
            matrix[r][0] = 1;
        }
    }
}""",
        "fixed_code": """public class OffByOneFix013 {
    public void iterateRows(int[][] matrix) {
        for (int r = 0; r < matrix.length; r++) {
            matrix[r][0] = 1;
        }
    }
}""",
        "notes": "2d array row iteration using <=",
    },
    {
        "type": "off_by_one",
        "id": 14,
        "buggy_class_name": "OffByOneBug014",
        "fixed_class_name": "OffByOneFix014",
        "buggy_code": """public class OffByOneBug014 {
    public void iterateCols(int[][] matrix) {
        for (int c = 0; c <= matrix[0].length; c++) {
            matrix[0][c] = 1;
        }
    }
}""",
        "fixed_code": """public class OffByOneFix014 {
    public void iterateCols(int[][] matrix) {
        for (int c = 0; c < matrix[0].length; c++) {
            matrix[0][c] = 1;
        }
    }
}""",
        "notes": "2d array col iteration using <=",
    },
    {
        "type": "off_by_one",
        "id": 15,
        "buggy_class_name": "OffByOneBug015",
        "fixed_class_name": "OffByOneFix015",
        "buggy_code": """public class OffByOneBug015 {
    public void skipByTwo(int[] arr) {
        for (int i = 0; i <= arr.length; i += 2) {
            System.out.println(arr[i]);
        }
    }
}""",
        "fixed_code": """public class OffByOneFix015 {
    public void skipByTwo(int[] arr) {
        for (int i = 0; i < arr.length; i += 2) {
            System.out.println(arr[i]);
        }
    }
}""",
        "notes": "skip by 2 iteration using <=",
    },

    # INCORRECT CONDITIONAL 011-015
    {
        "type": "incorrect_conditional_operator",
        "id": 11,
        "buggy_class_name": "IncorrectConditionalBug011",
        "fixed_class_name": "IncorrectConditionalFix011",
        "buggy_code": """public class IncorrectConditionalBug011 {
    public void checkStatus(boolean status) {
        while (status = true) {
            System.out.println("Running");
            break;
        }
    }
}""",
        "fixed_code": """public class IncorrectConditionalFix011 {
    public void checkStatus(boolean status) {
        while (status == true) {
            System.out.println("Running");
            break;
        }
    }
}""",
        "notes": "assignment inside while condition instead of equality",
    },
    {
        "type": "incorrect_conditional_operator",
        "id": 12,
        "buggy_class_name": "IncorrectConditionalBug012",
        "fixed_class_name": "IncorrectConditionalFix012",
        "buggy_code": """public class IncorrectConditionalBug012 {
    public void checkLength(int len) {
        if (len = 0) {
            return;
        }
    }
}""",
        "fixed_code": """public class IncorrectConditionalFix012 {
    public void checkLength(int len) {
        if (len == 0) {
            return;
        }
    }
}""",
        "notes": "assignment of integer 0 inside if condition",
    },
    {
        "type": "incorrect_conditional_operator",
        "id": 13,
        "buggy_class_name": "IncorrectConditionalBug013",
        "fixed_class_name": "IncorrectConditionalFix013",
        "buggy_code": """public class IncorrectConditionalBug013 {
    public void validateUser(Object user) {
        if (user = null) {
            throw new IllegalArgumentException();
        }
    }
}""",
        "fixed_code": """public class IncorrectConditionalFix013 {
    public void validateUser(Object user) {
        if (user == null) {
            throw new IllegalArgumentException();
        }
    }
}""",
        "notes": "assignment of null object inside if loop",
    },
    {
        "type": "incorrect_conditional_operator",
        "id": 14,
        "buggy_class_name": "IncorrectConditionalBug014",
        "fixed_class_name": "IncorrectConditionalFix014",
        "buggy_code": """public class IncorrectConditionalBug014 {
    public void multipleChecks(int a, int b) {
        if (a > 5 && b = 10) {
            System.out.println("Win");
        }
    }
}""",
        "fixed_code": """public class IncorrectConditionalFix014 {
    public void multipleChecks(int a, int b) {
        if (a > 5 && b == 10) {
            System.out.println("Win");
        }
    }
}""",
        "notes": "assignment operator mixed in logical && expression",
    },
    {
        "type": "incorrect_conditional_operator",
        "id": 15,
        "buggy_class_name": "IncorrectConditionalBug015",
        "fixed_class_name": "IncorrectConditionalFix015",
        "buggy_code": """public class IncorrectConditionalBug015 {
    public void parseVal(int val) {
        int z = (val = 5) ? 1 : 0;
    }
}""",
        "fixed_code": """public class IncorrectConditionalFix015 {
    public void parseVal(int val) {
        int z = (val == 5) ? 1 : 0;
    }
}""",
        "notes": "ternary condition with assignment instead of equality",
    },

    # ARRAY LENGTH INDEX MISUSE 011-015
    {
        "type": "array_length_index_misuse",
        "id": 11,
        "buggy_class_name": "ArrayIndexBug011",
        "fixed_class_name": "ArrayIndexFix011",
        "buggy_code": """public class ArrayIndexBug011 {
    public int getCombinedEnd(int[] arr1, int[] arr2) {
        int[] combined = new int[arr1.length + arr2.length];
        return combined[combined.length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix011 {
    public int getCombinedEnd(int[] arr1, int[] arr2) {
        int[] combined = new int[arr1.length + arr2.length];
        return combined[combined.length - 1];
    }
}""",
        "notes": "accessing end of dynamically combined array length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 12,
        "buggy_class_name": "ArrayIndexBug012",
        "fixed_class_name": "ArrayIndexFix012",
        "buggy_code": """public class ArrayIndexBug012 {
    public int[] getLastRow(int[][] matrix) {
        return matrix[matrix.length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix012 {
    public int[] getLastRow(int[][] matrix) {
        return matrix[matrix.length - 1];
    }
}""",
        "notes": "accessing matrix.length as row index",
    },
    {
        "type": "array_length_index_misuse",
        "id": 13,
        "buggy_class_name": "ArrayIndexBug013",
        "fixed_class_name": "ArrayIndexFix013",
        "buggy_code": """public class ArrayIndexBug013 {
    public int getLastSize(int[] sizes) {
        return sizes[sizes.length] * 2;
    }
}""",
        "fixed_code": """public class ArrayIndexFix013 {
    public int getLastSize(int[] sizes) {
        return sizes[sizes.length - 1] * 2;
    }
}""",
        "notes": "fetching size inside arithmetic expression ending at length",
    },
    {
        "type": "array_length_index_misuse",
        "id": 14,
        "buggy_class_name": "ArrayIndexBug014",
        "fixed_class_name": "ArrayIndexFix014",
        "buggy_code": """public class ArrayIndexBug014 {
    public int fetchBonus(int[] bonuses) {
        return bonuses[bonuses.length] + 5;
    }
}""",
        "fixed_code": """public class ArrayIndexFix014 {
    public int fetchBonus(int[] bonuses) {
        return bonuses[bonuses.length - 1] + 5;
    }
}""",
        "notes": "direct out of bounds in return addition expression",
    },
    {
        "type": "array_length_index_misuse",
        "id": 15,
        "buggy_class_name": "ArrayIndexBug015",
        "fixed_class_name": "ArrayIndexFix015",
        "buggy_code": """public class ArrayIndexBug015 {
    public void swapEnds(int[] arr) {
        int temp = arr[0];
        arr[0] = arr[arr.length];
        arr[arr.length] = temp;
    }
}""",
        "fixed_code": """public class ArrayIndexFix015 {
    public void swapEnds(int[] arr) {
        int temp = arr[0];
        arr[0] = arr[arr.length - 1];
        arr[arr.length - 1] = temp;
    }
}""",
        "notes": "swapping first and last elements uses arr.length directly",
    },

    # ARRAY LENGTH INDEX MISUSE 016-030 (new)
    {
        "type": "array_length_index_misuse",
        "id": 16,
        "buggy_class_name": "ArrayIndexBug016",
        "fixed_class_name": "ArrayIndexFix016",
        "buggy_code": """public class ArrayIndexBug016 {
    public int readLastCopyValue(int[] source) {
        int[] copy = new int[source.length];
        return copy[copy.length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix016 {
    public int readLastCopyValue(int[] source) {
        int[] copy = new int[source.length];
        return copy[copy.length - 1];
    }
}""",
        "notes": "reading last value from copied array using copy.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 17,
        "buggy_class_name": "ArrayIndexBug017",
        "fixed_class_name": "ArrayIndexFix017",
        "buggy_code": """public class ArrayIndexBug017 {
    public int getLastMark(int[] marks) {
        int last = marks[marks.length];
        return last;
    }
}""",
        "fixed_code": """public class ArrayIndexFix017 {
    public int getLastMark(int[] marks) {
        int last = marks[marks.length - 1];
        return last;
    }
}""",
        "notes": "assigning last element using marks.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 18,
        "buggy_class_name": "ArrayIndexBug018",
        "fixed_class_name": "ArrayIndexFix018",
        "buggy_code": """public class ArrayIndexBug018 {
    public void updateLast(int[] values) {
        values[values.length] = 99;
    }
}""",
        "fixed_code": """public class ArrayIndexFix018 {
    public void updateLast(int[] values) {
        values[values.length - 1] = 99;
    }
}""",
        "notes": "writing to last element using values.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 19,
        "buggy_class_name": "ArrayIndexBug019",
        "fixed_class_name": "ArrayIndexFix019",
        "buggy_code": """public class ArrayIndexBug019 {
    public int sumTail(int[] nums) {
        return nums[nums.length] + nums[0];
    }
}""",
        "fixed_code": """public class ArrayIndexFix019 {
    public int sumTail(int[] nums) {
        return nums[nums.length - 1] + nums[0];
    }
}""",
        "notes": "using nums.length directly inside arithmetic return expression",
    },
    {
        "type": "array_length_index_misuse",
        "id": 20,
        "buggy_class_name": "ArrayIndexBug020",
        "fixed_class_name": "ArrayIndexFix020",
        "buggy_code": """public class ArrayIndexBug020 {
    public void printTail(int[] data) {
        System.out.println(data[data.length]);
    }
}""",
        "fixed_code": """public class ArrayIndexFix020 {
    public void printTail(int[] data) {
        System.out.println(data[data.length - 1]);
    }
}""",
        "notes": "printing tail element using data.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 21,
        "buggy_class_name": "ArrayIndexBug021",
        "fixed_class_name": "ArrayIndexFix021",
        "buggy_code": """public class ArrayIndexBug021 {
    public boolean isLastPositive(int[] scores) {
        return scores[scores.length] > 0;
    }
}""",
        "fixed_code": """public class ArrayIndexFix021 {
    public boolean isLastPositive(int[] scores) {
        return scores[scores.length - 1] > 0;
    }
}""",
        "notes": "comparison against last element using scores.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 22,
        "buggy_class_name": "ArrayIndexBug022",
        "fixed_class_name": "ArrayIndexFix022",
        "buggy_code": """public class ArrayIndexBug022 {
    public int getRightEdge(int[][] grid) {
        return grid[0][grid[0].length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix022 {
    public int getRightEdge(int[][] grid) {
        return grid[0][grid[0].length - 1];
    }
}""",
        "notes": "2d array column access using grid[0].length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 23,
        "buggy_class_name": "ArrayIndexBug023",
        "fixed_class_name": "ArrayIndexFix023",
        "buggy_code": """public class ArrayIndexBug023 {
    public int[] getBottomRow(int[][] table) {
        return table[table.length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix023 {
    public int[] getBottomRow(int[][] table) {
        return table[table.length - 1];
    }
}""",
        "notes": "2d array row access using table.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 24,
        "buggy_class_name": "ArrayIndexBug024",
        "fixed_class_name": "ArrayIndexFix024",
        "buggy_code": """public class ArrayIndexBug024 {
    public int getTrimmedLast(int[] values) {
        int picked = values[values.length];
        return picked - 1;
    }
}""",
        "fixed_code": """public class ArrayIndexFix024 {
    public int getTrimmedLast(int[] values) {
        int picked = values[values.length - 1];
        return picked - 1;
    }
}""",
        "notes": "reading array.length index into temp variable before arithmetic",
    },
    {
        "type": "array_length_index_misuse",
        "id": 25,
        "buggy_class_name": "ArrayIndexBug025",
        "fixed_class_name": "ArrayIndexFix025",
        "buggy_code": """public class ArrayIndexBug025 {
    public void replaceLast(boolean[] flags) {
        flags[flags.length] = false;
    }
}""",
        "fixed_code": """public class ArrayIndexFix025 {
    public void replaceLast(boolean[] flags) {
        flags[flags.length - 1] = false;
    }
}""",
        "notes": "boolean array write using flags.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 26,
        "buggy_class_name": "ArrayIndexBug026",
        "fixed_class_name": "ArrayIndexFix026",
        "buggy_code": """public class ArrayIndexBug026 {
    public int bumpLast(int[] totals) {
        totals[totals.length] = totals[0] + 1;
        return totals[0];
    }
}""",
        "fixed_code": """public class ArrayIndexFix026 {
    public int bumpLast(int[] totals) {
        totals[totals.length - 1] = totals[0] + 1;
        return totals[0];
    }
}""",
        "notes": "assignment to last slot using totals.length directly",
    },
    {
        "type": "array_length_index_misuse",
        "id": 27,
        "buggy_class_name": "ArrayIndexBug027",
        "fixed_class_name": "ArrayIndexFix027",
        "buggy_code": """public class ArrayIndexBug027 {
    public int chooseEnd(int[] queue) {
        int selected = queue[queue.length];
        if (selected > 5) {
            return selected;
        }
        return 0;
    }
}""",
        "fixed_code": """public class ArrayIndexFix027 {
    public int chooseEnd(int[] queue) {
        int selected = queue[queue.length - 1];
        if (selected > 5) {
            return selected;
        }
        return 0;
    }
}""",
        "notes": "using queue.length directly before later conditional logic",
    },
    {
        "type": "array_length_index_misuse",
        "id": 28,
        "buggy_class_name": "ArrayIndexBug028",
        "fixed_class_name": "ArrayIndexFix028",
        "buggy_code": """public class ArrayIndexBug028 {
    public int getAbsoluteTail(int[] nums) {
        return Math.abs(nums[nums.length]);
    }
}""",
        "fixed_code": """public class ArrayIndexFix028 {
    public int getAbsoluteTail(int[] nums) {
        return Math.abs(nums[nums.length - 1]);
    }
}""",
        "notes": "method call argument uses nums.length directly as index",
    },
    {
        "type": "array_length_index_misuse",
        "id": 29,
        "buggy_class_name": "ArrayIndexBug029",
        "fixed_class_name": "ArrayIndexFix029",
        "buggy_code": """public class ArrayIndexBug029 {
    public int fallbackTail(int[] arr) {
        return arr.length > 0 ? arr[arr.length] : 0;
    }
}""",
        "fixed_code": """public class ArrayIndexFix029 {
    public int fallbackTail(int[] arr) {
        return arr.length > 0 ? arr[arr.length - 1] : 0;
    }
}""",
        "notes": "ternary expression uses arr.length directly as last index",
    },
    {
        "type": "array_length_index_misuse",
        "id": 30,
        "buggy_class_name": "ArrayIndexBug030",
        "fixed_class_name": "ArrayIndexFix030",
        "buggy_code": """public class ArrayIndexBug030 {
    public String readLast(String[] words) {
        return words[words.length];
    }
}""",
        "fixed_code": """public class ArrayIndexFix030 {
    public String readLast(String[] words) {
        return words[words.length - 1];
    }
}""",
        "notes": "string array last element access using words.length directly",
    },
]

CLEAN_SNIPPETS: List[Dict[str, str]] = [
    {
        "id": 7,
        "class_name": "Clean007",
        "code": """public class Clean007 {
    public void readMax(int[] arr) {
        int max = arr.length;
        int idx = 0;
        while(idx < max) {
            System.out.println(arr[idx]);
            idx++;
        }
    }
}""",
        "notes": "standard while loop with variables limit",
    },
    {
        "id": 8,
        "class_name": "Clean008",
        "code": """public class Clean008 {
    public int calculateSum(int[] arr) {
        int sum = 0;
        for(int num : arr) {
            sum += num;
        }
        return sum;
    }
}""",
        "notes": "enhanced for loop calculating sum without indices",
    },
    {
        "id": 9,
        "class_name": "Clean009",
        "code": """public class Clean009 {
    public boolean checkReady(boolean isReady) {
        if (isReady == true) {
            return true;
        }
        return false;
    }
}""",
        "notes": "proper equality check against boolean true",
    },
    {
        "id": 10,
        "class_name": "Clean010",
        "code": """public class Clean010 {
    public int getMiddleElement(int[] arr) {
        return arr[arr.length / 2];
    }
}""",
        "notes": "safe retrieval using arr.length divided by 2",
    },
    {
        "id": 11,
        "class_name": "Clean011",
        "code": """public class Clean011 {
    public void loopFromOne(int[] arr) {
        for(int i = 1; i < arr.length; i++) {
            arr[i] = arr[i - 1] + 1;
        }
    }
}""",
        "notes": "starts loop at 1 ending at < array length safely",
    },
]

# ----------------------------
# Helpers
# ----------------------------

def ensure_csv_exists() -> None:
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_FILE.exists():
        with CSV_FILE.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def load_existing_state() -> Tuple[Set[str], int]:
    ensure_csv_exists()

    existing_ids: Set[str] = set()
    max_pair_num = 0
    pair_pattern = re.compile(r"^pair_(\d+)$")

    with CSV_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            snippet_id = (row.get("snippet_id") or "").strip()
            if snippet_id:
                existing_ids.add(snippet_id)

            pair_group = (row.get("pair_group") or "").strip()
            match = pair_pattern.match(pair_group)
            if match:
                max_pair_num = max(max_pair_num, int(match.group(1)))

    return existing_ids, max_pair_num


def to_relative_project_path(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_java_file(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")


def build_snippet_id(snippet_type: str, role: str, snippet_num: int) -> str:
    prefix = PREFIX_MAP[snippet_type]
    return f"{prefix}_{role}_{snippet_num:03d}"


def append_row(
    writer: csv.DictWriter,
    snippet_id: str,
    file_path: str,
    primary_label: str,
    is_clean: str,
    has_off_by_one: str,
    has_incorrect_conditional: str,
    has_array_length_index_misuse: str,
    pair_group: str,
    pair_role: str,
    notes: str,
) -> None:
    writer.writerow(
        {
            "snippet_id": snippet_id,
            "file_path": file_path,
            "language": "java",
            "primary_label": primary_label,
            "is_clean": is_clean,
            "has_off_by_one": has_off_by_one,
            "has_incorrect_conditional": has_incorrect_conditional,
            "has_array_length_index_misuse": has_array_length_index_misuse,
            "pair_group": pair_group,
            "pair_role": pair_role,
            "source_type": "manual_curated",
            "notes": notes,
        }
    )


def add_pair_snippets() -> Tuple[int, int, int]:
    existing_ids, max_pair_num = load_existing_state()
    next_pair_num = max_pair_num + 1

    added_buggy = 0
    added_fixed = 0
    skipped_pairs = 0

    with CSV_FILE.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        for snippet in PAIR_SNIPPETS:
            snippet_type = snippet["type"]
            buggy_id = build_snippet_id(snippet_type, "bug", snippet["id"])
            fixed_id = build_snippet_id(snippet_type, "fix", snippet["id"])

            buggy_path = (
                BASE_PATH
                / "raw_snippets"
                / snippet_type
                / "buggy"
                / f"{snippet['buggy_class_name']}.java"
            )
            fixed_path = (
                BASE_PATH
                / "raw_snippets"
                / snippet_type
                / "fixed"
                / f"{snippet['fixed_class_name']}.java"
            )

            # Always recreate the java files from this source file
            write_java_file(buggy_path, snippet["buggy_code"])
            write_java_file(fixed_path, snippet["fixed_code"])

            # Only append metadata if missing
            if buggy_id in existing_ids or fixed_id in existing_ids:
                skipped_pairs += 1
                continue

            pair_group = f"pair_{next_pair_num:03d}"
            next_pair_num += 1

            has_off_by_one = "1" if snippet_type == "off_by_one" else "0"
            has_incorrect_conditional = "1" if snippet_type == "incorrect_conditional_operator" else "0"
            has_array_length_index_misuse = "1" if snippet_type == "array_length_index_misuse" else "0"

            append_row(
                writer=writer,
                snippet_id=buggy_id,
                file_path=to_relative_project_path(buggy_path),
                primary_label=LABEL_MAP[snippet_type],
                is_clean="0",
                has_off_by_one=has_off_by_one,
                has_incorrect_conditional=has_incorrect_conditional,
                has_array_length_index_misuse=has_array_length_index_misuse,
                pair_group=pair_group,
                pair_role="buggy",
                notes=snippet["notes"],
            )
            added_buggy += 1

            append_row(
                writer=writer,
                snippet_id=fixed_id,
                file_path=to_relative_project_path(fixed_path),
                primary_label="NO_ISSUE",
                is_clean="1",
                has_off_by_one="0",
                has_incorrect_conditional="0",
                has_array_length_index_misuse="0",
                pair_group=pair_group,
                pair_role="fixed",
                notes="fixed: " + snippet["notes"],
            )
            added_fixed += 1

            existing_ids.add(buggy_id)
            existing_ids.add(fixed_id)

    return added_buggy, added_fixed, skipped_pairs


def add_clean_snippets() -> Tuple[int, int]:
    existing_ids, _ = load_existing_state()
    added_clean = 0
    skipped_clean = 0

    with CSV_FILE.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        for clean in CLEAN_SNIPPETS:
            clean_id = f"clean_{clean['id']:03d}"
            clean_path = BASE_PATH / "raw_snippets" / "clean" / f"{clean['class_name']}.java"

            # Always recreate the java file from this source file
            write_java_file(clean_path, clean["code"])

            # Only append metadata if missing
            if clean_id in existing_ids:
                skipped_clean += 1
                continue

            append_row(
                writer=writer,
                snippet_id=clean_id,
                file_path=to_relative_project_path(clean_path),
                primary_label="NO_ISSUE",
                is_clean="1",
                has_off_by_one="0",
                has_incorrect_conditional="0",
                has_array_length_index_misuse="0",
                pair_group="",
                pair_role="clean",
                notes=clean["notes"],
            )
            added_clean += 1
            existing_ids.add(clean_id)

    return added_clean, skipped_clean


def main() -> None:
    ensure_csv_exists()

    added_buggy, added_fixed, skipped_pairs = add_pair_snippets()
    added_clean, skipped_clean = add_clean_snippets()

    print("Done.")
    print(f"Added buggy rows: {added_buggy}")
    print(f"Added fixed rows: {added_fixed}")
    print(f"Skipped existing pairs: {skipped_pairs}")
    print(f"Added clean rows: {added_clean}")
    print(f"Skipped existing clean rows: {skipped_clean}")


if __name__ == "__main__":
    main()