package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug025 {
    public void printEven(int[] arr) {
        for (int i = 0; i <= arr.length; i += 2) {
            System.out.println(arr[i]);
        }
    }
}
