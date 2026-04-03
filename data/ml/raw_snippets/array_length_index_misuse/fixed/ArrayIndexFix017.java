package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix017 {
    public int getLastMark(int[] marks) {
        int last = marks[marks.length - 1];
        return last;
    }
}