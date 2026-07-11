public class GenArrayIndexFix034 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length - 1] = value;
    }

    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }
}
