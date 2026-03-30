package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix002 {
    public static void main(String[] args) {
        String[] names = { "A", "B", "C" };

        System.out.println(names[names.length - 1]);
    }
}