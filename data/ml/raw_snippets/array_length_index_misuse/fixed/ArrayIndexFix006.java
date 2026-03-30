package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix006 {
    public static void main(String[] args) {
        String[] letters = { "A", "B", "C", "D" };

        System.out.println(letters[letters.length - 1]);
    }
}