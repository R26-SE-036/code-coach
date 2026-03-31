package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug008 {
    public static void main(String[] args) {
        char[] letters = { 'A', 'B', 'C' };
        int index = letters.length;

        System.out.println(letters[index]);
    }
}
