package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix020 {
    public void printTail(int[] data) {
        System.out.println(data[data.length - 1]);
    }
}