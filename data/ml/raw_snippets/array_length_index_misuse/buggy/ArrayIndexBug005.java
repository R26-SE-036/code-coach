package data.ml.raw_snippets.array_length_index_misuse.buggy;

public class ArrayIndexBug005 {
    public static void main(String[] args) {
        int[] grades = { 55, 60, 75, 80 };
        int index = grades.length;

        System.out.println(grades[index]);
    }
}