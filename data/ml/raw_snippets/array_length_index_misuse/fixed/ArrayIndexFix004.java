package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix004 {
    public static void main(String[] args) {
        int[] numbers = { 11, 22, 33 };

        int lastValue = numbers[numbers.length - 1];
        System.out.println(lastValue);
    }
}