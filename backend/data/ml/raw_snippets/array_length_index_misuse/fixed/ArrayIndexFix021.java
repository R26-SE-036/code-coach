public class ArrayIndexFix021 {
    public boolean isLastPositive(int[] scores) {
        return scores[scores.length - 1] > 0;
    }
}