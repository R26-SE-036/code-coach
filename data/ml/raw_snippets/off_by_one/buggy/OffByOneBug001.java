package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug001 {
    public static void main(String[] args) {
        int[] arr = { 1, 2, 3 };

        for (int i = 0; i <= arr.length; i++) {
            System.out.println(arr[i]);
        }
    }
}