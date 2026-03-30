package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix001 {
    public static void main(String[] args) {
        int[] arr = { 1, 2, 3 };

        System.out.println(arr[arr.length - 1]);
    }
}
