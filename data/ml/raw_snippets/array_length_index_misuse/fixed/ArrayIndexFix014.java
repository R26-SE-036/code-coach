package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix014 {
    public boolean getLastStatus(boolean[] flags) {
        return flags[flags.length - 1];
    }
}
