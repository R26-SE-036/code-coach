package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug018 {
    public boolean contains(int[] arr, int target) {
        for (int i = 0; i <= arr.length; i++) {
            if (arr[i] == target)
                return true;
        }
        return false;
    }
}
