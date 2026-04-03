package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug023 {
    public int[] shiftRight(int[] arr) {
        int[] result = new int[arr.length];
        for (int i = 0; i <= arr.length - 1; i++) {
            result[i + 1] = arr[i];
        }
        return result;
    }
}
