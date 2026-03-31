package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix009 {
    public static void main(String[] args) {
        boolean[] flags = { true, false, true };

        if (flags[flags.length - 1]) {
            System.out.println("Last flag is true");
        }
    }
}
