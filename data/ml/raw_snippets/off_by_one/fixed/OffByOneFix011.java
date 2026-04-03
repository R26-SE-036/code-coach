package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length - 1; i >= 0; i--) {
            System.out.println(arr[i]);
        }
    }
}