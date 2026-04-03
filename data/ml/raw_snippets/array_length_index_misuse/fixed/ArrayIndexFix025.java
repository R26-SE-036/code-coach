package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix025 {
    public void replaceLast(boolean[] flags) {
        flags[flags.length - 1] = false;
    }
}