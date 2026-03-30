package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix005 {
    public static void main(String[] args) {
        int[] grades = { 55, 60, 75, 80 };
        int index = grades.length - 1;

        System.out.println(grades[index]);
    }
}
