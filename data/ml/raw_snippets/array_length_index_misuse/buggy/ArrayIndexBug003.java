package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug003 {
    public static void main(String[] args) {
        int[] values = { 7, 8, 9, 10 };
        int index = values.length;

        System.out.println(values[index]);
    }
}