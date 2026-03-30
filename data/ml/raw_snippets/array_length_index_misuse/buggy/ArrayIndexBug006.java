package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug006 {
    public static void main(String[] args) {
        String[] letters = { "A", "B", "C", "D" };

        System.out.println(letters[letters.length]);
    }
}