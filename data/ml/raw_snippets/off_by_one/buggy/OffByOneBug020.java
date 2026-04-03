package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug020 {
    public void fillZero(int[] arr) {
        for (int i = 0; i <= arr.length; i++) {
            arr[i] = 0;
        }
    }
}
