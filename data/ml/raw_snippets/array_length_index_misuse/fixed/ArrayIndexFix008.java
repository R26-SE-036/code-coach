package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix008 {
    public static void main(String[] args) {
        char[] letters = { 'A', 'B', 'C' };
        int index = letters.length - 1;

        System.out.println(letters[index]);
    }
}
