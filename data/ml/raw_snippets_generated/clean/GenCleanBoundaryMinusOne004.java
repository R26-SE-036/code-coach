public class GenCleanBoundaryMinusOne004 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static int tally(int[] ratings) {
        int total = 0;
        for (int i = 0; i <= ratings.length - 1; i++) {
            total += ratings[i];
        }
        return total;
    }
}
