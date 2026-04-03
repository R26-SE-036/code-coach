package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug017 {
    public void doubleValues(int[] arr) {
        for (int i = 0; i <= arr.length; i++) {
            arr[i] = arr[i] * 2;
        }
    }
}
