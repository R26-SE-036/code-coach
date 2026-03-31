package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix010 {
    public static void main(String[] args) {
        int[] ages = { 19, 21, 22, 25 };
        int oldest = ages[ages.length - 1];

        System.out.println(oldest);
    }
}
