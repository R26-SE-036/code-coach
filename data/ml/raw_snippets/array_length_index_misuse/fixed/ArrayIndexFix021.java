package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix021 {
    public boolean isLastPositive(int[] scores) {
        return scores[scores.length - 1] > 0;
    }
}