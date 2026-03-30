package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix003 {
    public static void main(String[] args) {
        int[] values = { 7, 8, 9, 10 };
        int index = values.length - 1;

        System.out.println(values[index]);
    }
}