package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug010 {
    public static void main(String[] args) {
        int[] ages = { 19, 21, 22, 25 };
        int oldest = ages[ages.length];

        System.out.println(oldest);
    }
}
