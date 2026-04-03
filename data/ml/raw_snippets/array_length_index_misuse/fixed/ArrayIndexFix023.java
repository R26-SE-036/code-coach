package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix023 {
    public int[] getBottomRow(int[][] table) {
        return table[table.length - 1];
    }
}