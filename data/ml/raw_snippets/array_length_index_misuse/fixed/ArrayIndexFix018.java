package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix018 {
    public void updateLast(int[] values) {
        values[values.length - 1] = 99;
    }
}