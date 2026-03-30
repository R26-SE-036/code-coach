package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug004 {
    public static void main(String[] args) {
        int[] numbers = { 11, 22, 33 };

        int lastValue = numbers[numbers.length];
        System.out.println(lastValue);
    }
}