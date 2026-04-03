package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix028 {
    public int countEven(int[] arr) {
        int count = 0;
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] % 2 == 0)
                count++;
        }
        return count;
    }
}
