package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix016 {
    public int readLastCopyValue(int[] source) {
        int[] copy = new int[source.length];
        return copy[copy.length - 1];
    }
}