package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix026 {
    public int bumpLast(int[] totals) {
        totals[totals.length - 1] = totals[0] + 1;
        return totals[0];
    }
}