package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug021 {
    public int product(int[] factors) {
        int result = 1;
        for (int i = 0; i <= factors.length; i++) {
            result *= factors[i];
        }
        return result;
    }
}
