package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug004 {
    public static void main(String[] args) {
        int[] data = { 4, 5, 6 };
        int[] copy = new int[data.length];

        for (int i = 0; i <= data.length; i++) {
            copy[i] = data[i];
        }
    }
}