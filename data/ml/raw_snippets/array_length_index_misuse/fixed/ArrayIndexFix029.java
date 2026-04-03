package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix029 {
    public int fallbackTail(int[] arr) {
        return arr.length > 0 ? arr[arr.length - 1] : 0;
    }
}