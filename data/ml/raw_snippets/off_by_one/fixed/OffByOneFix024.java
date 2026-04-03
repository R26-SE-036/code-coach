package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix024 {
    public int average(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total / scores.length;
    }
}
