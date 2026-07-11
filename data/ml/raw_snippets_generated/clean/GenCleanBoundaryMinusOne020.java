public class GenCleanBoundaryMinusOne020 {
    static String describe1(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] weights) {
        int total = 0;
        for (int i = 0; i <= weights.length - 1; i++) {
            total += weights[i];
        }
        return total;
    }
}
