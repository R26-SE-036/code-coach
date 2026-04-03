public class ArrayIndexBug021 {
    public boolean isLastPositive(int[] scores) {
        return scores[scores.length] > 0;
    }
}