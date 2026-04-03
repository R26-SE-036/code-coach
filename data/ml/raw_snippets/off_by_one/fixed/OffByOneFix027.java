package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix027 {
    public void negateAll(int[] arr) {
        for (int i = 0; i < arr.length; i++) {
            arr[i] = -arr[i];
        }
    }
}
