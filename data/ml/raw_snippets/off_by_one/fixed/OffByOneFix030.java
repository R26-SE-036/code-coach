package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix030 {
    public int lastIndex(int[] arr, int target) {
        int idx = -1;
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] == target)
                idx = i;
        }
        return idx;
    }
}
