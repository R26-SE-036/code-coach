package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix016 {
    public int findMin(int[] arr) {
        int min = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] < min)
                min = arr[i];
        }
        return min;
    }
}
