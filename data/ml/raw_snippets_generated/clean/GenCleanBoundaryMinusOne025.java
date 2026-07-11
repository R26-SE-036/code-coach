public class GenCleanBoundaryMinusOne025 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describe2(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] ratings) {
        int total = 0;
        for (int i = 0; i <= ratings.length - 1; i++) {
            total += ratings[i];
        }
        return total;
    }
}
