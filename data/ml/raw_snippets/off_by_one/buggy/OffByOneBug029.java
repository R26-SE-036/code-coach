package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug029 {
    public void incrementAll(int[] arr) {
        for (int i = 0; i <= arr.length; i++) {
            arr[i]++;
        }
    }
}
