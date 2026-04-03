package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while (left <= right.length) {
            left++;
        }
    }
}