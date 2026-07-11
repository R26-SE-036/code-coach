public class GenCleanBoundaryMinusOne007 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int tally(int[] ages) {
        int total = 0;
        for (int i = 0; i <= ages.length - 1; i++) {
            total += ages[i];
        }
        return total;
    }

    static String describe2(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }
}
